"""Post-publication snapshot of immutable tested native images; no registry writes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
from common import ROOT, matrix, write_json
from publish import publication_plan, REPOSITORY, VARIANTS
from security import evaluate

def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda:source.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()

def archive_reports(folder,arch):
    names=['scan-metadata.json','scan-summary.md','trivy-db-metadata.json']
    names += [f'{kind}-{major}.{suffix}' for major in VARIANTS
              for kind,suffix in [('trivy','json'),('security','json'),('sbom','cdx.json')]]
    target=folder/f'scan-{arch}.tar.gz'
    with tarfile.open(target,'w:gz') as archive:
        for name in names:
            path=folder/name
            if path.is_symlink():raise ValueError('Refusing symlink scan artifact')
            if path.is_file():archive.add(path,arcname=name,recursive=False)
    return target

def summary(metadata):
    lines=[f"# Published image scan: {metadata['release']} / {metadata['arch']}",
           '', 'Published images remain available regardless of scan findings.', '',
           '| Ansible | Status | High/Critical requiring review | Accepted | Native digest |',
           '| --- | --- | ---: | ---: | --- |']
    for major,row in metadata['images'].items():
        lines.append(f"| {major} | {row['status']} | {row.get('highCritical','—')} | {row.get('accepted','—')} | `{row['digest']}` |")
    if metadata.get('error'):lines.extend(['', 'Scanner initialization failed; see scan-metadata.json and job logs.'])
    return '\n'.join(lines)+'\n'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--arch',choices=['amd64','arm64'],required=True)
    args=parser.parse_args()
    release=os.environ['PLATFORM_VERSION']
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    plan=publication_plan(args.directory,release,revision,root=ROOT)
    folder=ROOT/'.build/published-scan'/args.arch;folder.mkdir(parents=True,exist_ok=True)
    # Clear only this scanner's explicit outputs so failed retries cannot export stale findings.
    for name in ['scan-metadata.json','scan-summary.md','trivy-db-metadata.json',f'scan-{args.arch}.tar.gz'] + [f'{kind}-{major}.{suffix}' for major in VARIANTS for kind,suffix in [('trivy','json'),('security','json'),('sbom','cdx.json')]]:
        path=folder/name
        if path.exists() or path.is_symlink():path.unlink()
    cache=ROOT/'.build/trivy-cache';cache.mkdir(exist_ok=True)
    scanner=matrix()['security']['trivyImage']
    command=['docker','run','--rm','-v','/var/run/docker.sock:/var/run/docker.sock',
             '-v',f'{folder}:/reports','-v',f'{cache}:/cache','-e','TRIVY_CACHE_DIR=/cache',scanner]
    metadata={'release':release,'arch':args.arch,'revision':revision,'scanner':scanner,
              'startedAt':datetime.now(timezone.utc).isoformat(),
              'runId':os.environ.get('GITHUB_RUN_ID'),'runAttempt':os.environ.get('GITHUB_RUN_ATTEMPT'),
              'policySha256':sha(ROOT/'scripts/security.py'),
              'images':{major:{'digest':plan[major][args.arch],
                               'reference':REPOSITORY+'@'+plan[major][args.arch],
                               'status':'not_scanned'} for major in VARIANTS}}
    failed=False
    try:
        subprocess.run([*command,'image','--download-db-only'],check=True)
        metadata['scannerVersion']=subprocess.check_output([*command,'--version'],text=True)
        db=cache/'db/trivy.db';db_metadata=cache/'db/metadata.json'
        metadata['databaseSha256']=sha(db)
        write_json(folder/'trivy-db-metadata.json',json.loads(db_metadata.read_text()))
        for major in VARIANTS:
            digest=plan[major][args.arch];reference=REPOSITORY+'@'+digest
            row=metadata['images'][major];row['status']='error'
            existed=subprocess.run(['docker','image','inspect',reference],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
            try:
                subprocess.run(['docker','pull','--platform','linux/'+args.arch,reference],check=True)
                subprocess.run([*command,'image','--skip-db-update','--image-src','docker','--scanners','vuln',
                                '--list-all-pkgs','--format','json','--output',f'/reports/trivy-{major}.json',reference],check=True)
                raw=folder/f'trivy-{major}.json'
                result=evaluate(json.loads(raw.read_text()),major)
                write_json(folder/f'security-{major}.json',result)
                subprocess.run([*command,'convert','--format','cyclonedx','--output',f'/reports/sbom-{major}.cdx.json',f'/reports/{raw.name}'],check=True)
                row.update(status='findings' if result['blocked'] else 'pass',highCritical=len(result['blocked']),
                           accepted=len(result['accepted']),reportSha256=sha(raw))
                failed=failed or bool(result['blocked'])
            except (subprocess.CalledProcessError,ValueError,OSError) as error:
                row['error']=str(error);failed=True
            finally:
                if not existed:subprocess.run(['docker','image','rm',reference],check=False)
    except (subprocess.CalledProcessError,ValueError,OSError) as error:
        metadata['error']=str(error);failed=True
    finally:
        metadata['finishedAt']=datetime.now(timezone.utc).isoformat()
        write_json(folder/'scan-metadata.json',metadata)
        text=summary(metadata)
        (folder/'scan-summary.md').write_text(text)
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as target:target.write(text)
        archive_reports(folder,args.arch)
    if failed:raise SystemExit(1)

if __name__=='__main__':main()
