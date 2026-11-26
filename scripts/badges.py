"""Render vulnerability badges from existing CI snapshots; never build or scan images."""
import argparse
import copy
import json
import os
from pathlib import Path
import re
from urllib.parse import quote
from common import ROOT, read_json, write_json
from version import validate

START='<!-- security-badges:start -->'
END='<!-- security-badges:end -->'
ARCHES=('amd64','arm64')
VARIANTS=('10','12','14')

def collect(directory,release,revision,run_id,repository):
    validate(release)
    if not re.fullmatch(r'[a-f0-9]{40}',revision):raise ValueError('Invalid image source revision')
    if not re.fullmatch(r'[1-9][0-9]*',str(run_id)):raise ValueError('Invalid workflow run ID')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository):raise ValueError('Invalid repository')
    selected={};seen=set();directory=Path(directory)
    for path in sorted(directory.rglob('scan-metadata.json')):
        if path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError('Refusing a scan metadata symlink')
        data=read_json(path)
        if (data['release'],data['revision'],str(data['runId']))!=(release,revision,str(run_id)):
            raise ValueError('Scan snapshot identity differs from the requested release/run')
        arch=data['arch'];attempt=str(data['runAttempt'])
        if arch not in ARCHES or not re.fullmatch(r'[1-9][0-9]*',attempt):raise ValueError('Invalid architecture/attempt')
        key=(arch,int(attempt))
        if key in seen:raise ValueError('Duplicate scan architecture/attempt')
        seen.add(key)
        if arch not in selected or int(attempt)>int(selected[arch]['runAttempt']):selected[arch]=data
    missing_attempts={}
    pattern=r'security-(\d{4}\.\d{2}\.\d{2}(?:-[1-9]\d*)?)-(amd64|arm64)-attempt([1-9]\d*)'
    for folder in [directory,*directory.rglob('*')]:
        match=re.fullmatch(pattern,folder.name)
        if not match or not folder.is_dir():continue
        if folder.is_symlink() or not folder.resolve().is_relative_to(directory.resolve()):
            raise ValueError('Refusing a scan artifact directory symlink')
        artifact_release,arch,attempt=match.groups()
        if artifact_release!=release:raise ValueError('Artifact release differs from requested release')
        metadata_path=folder/'scan-metadata.json'
        if metadata_path.exists():
            data=read_json(metadata_path)
            if (data['arch'],str(data['runAttempt']))!=(arch,attempt):
                raise ValueError('Artifact name differs from snapshot identity')
        else:missing_attempts[arch]=max(missing_attempts.get(arch,0),int(attempt))
    snapshot={'schemaVersion':1,'release':release,'revision':revision,'runId':str(run_id),
              'repository':repository,'runUrl':f'https://github.com/{repository}/actions/runs/{run_id}',
              'architectures':{}}
    for arch in ARCHES:
        data=selected.get(arch)
        missing_attempt=missing_attempts.get(arch,0)
        if data is None or missing_attempt>int(data['runAttempt']):
            snapshot['architectures'][arch]={'runAttempt':str(missing_attempt) if missing_attempt else None,
                'images':{v:{'status':'not_scanned','highCritical':None} for v in VARIANTS}}
            continue
        images={}
        if set(data['images'])!=set(VARIANTS):raise ValueError('Incomplete variant identities')
        for major,row in data['images'].items():
            status=row['status']
            if status not in ('pass','findings','error','not_scanned'):raise ValueError('Unknown scan status')
            if not re.fullmatch(r'sha256:[a-f0-9]{64}',row['digest']):raise ValueError('Missing immutable image digest')
            count=row.get('highCritical') if status in ('pass','findings') else None
            if status in ('pass','findings'):
                if type(count) is not int or count<0 or (status=='pass')!=(count==0):
                    raise ValueError('Invalid completed scan count/status')
            images[major]={'status':status,'highCritical':count,'accepted':row.get('accepted'),
                           'digest':row['digest'],'reportSha256':row.get('reportSha256')}
        snapshot['architectures'][arch]={key:data.get(key) for key in
            ('runAttempt','startedAt','finishedAt','scanner','databaseSha256','policySha256')}
        snapshot['architectures'][arch]['images']=images
    return snapshot

def keep_newer(candidate,current):
    def version_key(value):
        validate(value)
        date,_,suffix=value.partition('-')
        return (*map(int,date.split('.')),int(suffix or 0))
    incoming=(version_key(candidate['release']),int(candidate['runId']))
    existing=(version_key(current['release']),int(current['runId']))
    if incoming<existing:return current
    if incoming>existing:return candidate
    if candidate['revision']!=current['revision']:raise ValueError('One run cannot have different source revisions')
    merged=copy.deepcopy(candidate)
    for arch in ARCHES:
        old=current['architectures'][arch];new=candidate['architectures'][arch]
        if int(old.get('runAttempt') or 0)>int(new.get('runAttempt') or 0):
            merged['architectures'][arch]=copy.deepcopy(old)
    return merged

def markdown(snapshot):
    url=snapshot['runUrl'];release=snapshot['release']
    lines=[START,f'[![Trivy: {release}](https://img.shields.io/badge/Trivy-{release}-blue?style=flat-square)]({url})',
           '', '| Ansible | amd64 | arm64 |','| --- | --- | --- |']
    for major in VARIANTS:
        cells=[]
        for arch in ARCHES:
            row=snapshot['architectures'][arch]['images'][major]
            count=row['highCritical']
            if row['status'] in ('pass','findings') and type(count) is int:
                message=f'{count} High/Critical';color='red' if count else 'brightgreen'
            else:message='scan error';color='lightgrey'
            image=f'https://img.shields.io/badge/{arch}-{quote(message,safe="")}-{color}?style=flat-square'
            cells.append(f'[![Ansible {major} {arch}: {message}]({image})]({url})')
        lines.append('| '+major+' | '+' | '.join(cells)+' |')
    lines.extend(['','Счётчики находок High/Critical учитывают согласованные исключения Ansible 10.',
                  f'Полные JSON/SBOM — в [Artifacts этого скана]({url}#artifacts).',END])
    return '\n'.join(lines)

def replace_block(text,snapshot):
    if text.count(START)!=1 or text.count(END)!=1 or text.index(START)>text.index(END):
        raise ValueError('Expected one README security badge block')
    begin=text.index(START);end=text.index(END)+len(END)
    return text[:begin]+markdown(snapshot)+text[end:]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path)
    parser.add_argument('--release',default=os.environ.get('PLATFORM_VERSION'))
    parser.add_argument('--revision',default=os.environ.get('GITHUB_SHA'))
    parser.add_argument('--run-id',default=os.environ.get('GITHUB_RUN_ID'))
    parser.add_argument('--repository',default=os.environ.get('GITHUB_REPOSITORY','WeslyG/devcontainer-ansible'))
    args=parser.parse_args();record=ROOT/'compatibility/security-snapshot.json'
    if args.directory:
        if not all((args.release,args.revision,args.run_id)):parser.error('Existing snapshots require release, revision and run ID')
        snapshot=collect(args.directory,args.release,args.revision,args.run_id,args.repository)
        if record.exists():snapshot=keep_newer(snapshot,read_json(record))
    else:snapshot=read_json(record)
    readme=ROOT/'README.md';text=replace_block(readme.read_text(),snapshot)
    write_json(record,snapshot);readme.write_text(text)
    print('Updated README badges from existing snapshots; no build or scan was run.')

if __name__=='__main__':main()
