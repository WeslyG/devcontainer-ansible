"""Push tested native images and assemble verified multiarch release tags."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from common import ROOT, read_json, run, write_json
from version import REPOSITORY, registry_tags, validate

ARCHES=('amd64','arm64')
VARIANTS=('10','12','14')

def require(condition,message):
    if not condition:raise ValueError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def release_tag(major,release):
    require(major in VARIANTS,'Unknown Ansible variant')
    return f'{REPOSITORY}:ansible{major}-{validate(release)}'

def native_tag(major,arch,release):
    require(major in VARIANTS and arch in ARCHES,'Unknown variant/architecture')
    return f'{REPOSITORY}:{arch}-ansible{major}-{validate(release)}'

def checked_result(major,arch,release,root=ROOT):
    require(arch in ARCHES,'Unknown native architecture')
    validate(release)
    data=read_json(root/'images.json')
    row=read_json(root/f'.build/{arch}/results.json')['images'][major]
    require(row.get('tested') is True,'Publication requires successful native tests')
    require(row.get('platform')=='linux/'+arch,'Test platform differs from publication platform')
    require(row.get('platformVersion')==release,'Release differs from tested version')
    require(row.get('image')==f'ansible-infra:ansible{major}-{release}','Unexpected tested image tag')
    require(row.get('manifestSha256')==sha(root/'images.json'),'Dependency manifest differs from tested input')
    require(row.get('lockSha256')==sha(root/f'requirements/ansible{major}.txt'),'Python lock differs from tested input')
    require(row.get('pythonImage')==data['variants'][major]['pythonImage'],'Controller image differs from tested input')
    require(0<row['bytes']<=data['variants'][major]['maxImageBytes'],'Image exceeds reviewed size budget')
    require(re.fullmatch(r'sha256:[a-f0-9]{64}',row.get('imageId','')),'Missing tested image ID')
    return row

def matches_image_config(remote,local):
    # Docker's classic store uses a config digest as Image ID; containerd can
    # use an index/manifest digest. Compare content independently of that alias.
    def configuration(value):
        return {key:item for key,item in (value or {}).items() if item not in (None,'',[],{},False,0)}
    return (remote.get('Os')==local['Os'] and remote.get('Architecture')==local['Architecture']
            and remote.get('RootFS',{}).get('Layers',[])==local['RootFS'].get('Layers',[])
            and configuration(remote.get('Config'))==configuration(local['Config']))

def verify_native(tag,local):
    descriptor=json.loads(subprocess.check_output(['docker','buildx','imagetools','inspect','--format','{{json .Manifest}}',tag],text=True))
    digest=descriptor['digest']
    require(re.fullmatch(r'sha256:[a-f0-9]{64}',digest),'Invalid native manifest digest')
    reference=REPOSITORY+'@'+digest
    manifest=inspect_manifest(reference)
    require('config' in manifest and 'manifests' not in manifest,'Expected a single native manifest')
    # Pull by immutable digest into the already populated daemon store. Inspect
    # the full Docker config: the OCI-only imagetools .Image view omits Shell,
    # Healthcheck and other Docker-specific fields. Existing layers are reused.
    run(['docker','image','pull','--platform','linux/'+local['Architecture'],reference])
    remote=json.loads(subprocess.check_output(['docker','image','inspect',reference]))[0]
    require(matches_image_config(remote,local),f'Published filesystem/configuration differs from tested image: {tag}')
    return digest,manifest['config']['digest']

def stage(major,arch,release):
    row=checked_result(major,arch,release,root=ROOT)
    inspected=json.loads(subprocess.check_output(['docker','image','inspect',row['image']]))[0]
    require(inspected['Id']==row['imageId'],'Image changed after tests')
    require(inspected['Os']=='linux' and inspected['Architecture']==arch,'Loaded image has unexpected architecture')
    require(f'PLATFORM_VERSION={release}' in inspected['Config']['Env'],'Image environment differs from release')
    require(inspected['Config']['Labels']['org.opencontainers.image.version']==release,'OCI version differs from release')
    tag=native_tag(major,arch,release)
    existing=set(registry_tags(release.split('-')[0]))
    if tag.rsplit(':',1)[1] in existing:
        verify_native(tag,inspected)
    else:
        run(['docker','image','tag',row['image'],tag])
        # Select a single native manifest even when the daemon uses a containerd
        # store. Push the loaded image that passed tests, without a rebuild/export.
        run(['docker','image','push','--platform','linux/'+arch,tag])
    digest,config_digest=verify_native(tag,inspected)
    require(re.fullmatch(r'sha256:[a-f0-9]{64}',config_digest),'Invalid published config digest')
    require(re.fullmatch(r'sha256:[a-f0-9]{64}',digest),'Invalid exported digest')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    record={**row,'variant':major,'arch':arch,'repository':REPOSITORY,'digest':digest,'revision':revision,'nativeTag':tag,'imageConfigDigest':config_digest}
    write_json(ROOT/f'.build/{arch}/publish-{major}-{arch}.json',record)
    print(f'Uploaded tested image: {tag}@{digest}',flush=True)

def publication_plan(directory,release,revision,root=ROOT):
    validate(release)
    manifest=sha(root/'images.json')
    data=read_json(root/'images.json')
    plan={}
    for major in VARIANTS:
        plan[major]={}
        for arch in ARCHES:
            path=directory/f'validation-ansible{major}-{release}-{arch}'/f'publish-{major}-{arch}.json'
            require(not path.is_symlink(),'Publication record must be a regular file')
            row=read_json(path)
            require(row.get('tested') is True,'Missing successful native tests')
            require(row.get('variant')==major and row.get('arch')==arch,'Artifact variant/architecture mismatch')
            require(row.get('platform')=='linux/'+arch,'Artifact platform mismatch')
            require(row.get('platformVersion')==release and row.get('revision')==revision,'Artifact release/revision mismatch')
            require(row.get('repository')==REPOSITORY,'Unexpected registry repository')
            require(row.get('nativeTag')==native_tag(major,arch,release),'Artifact native tag mismatch')
            require(row.get('image')==f'ansible-infra:ansible{major}-{release}','Artifact image tag mismatch')
            require(row.get('manifestSha256')==manifest,'Artifact uses another dependency manifest')
            require(row.get('lockSha256')==sha(root/f'requirements/ansible{major}.txt'),'Artifact uses another Python lock')
            require(row.get('pythonImage')==data['variants'][major]['pythonImage'],'Artifact controller mismatch')
            require(0<row['bytes']<=data['variants'][major]['maxImageBytes'],'Artifact exceeds size budget')
            require(re.fullmatch(r'sha256:[a-f0-9]{64}',row.get('digest','')),'Invalid image digest')
            require(re.fullmatch(r'sha256:[a-f0-9]{64}',row.get('imageId','')),'Missing tested image identity')
            require(re.fullmatch(r'sha256:[a-f0-9]{64}',row.get('imageConfigDigest','')),'Missing published config digest')
            plan[major][arch]=row['digest']
        require(len(set(plan[major].values()))==2,'Native image digests must be distinct')
    return plan

def matches_manifest(document,digests):
    entries=document.get('manifests',[])
    return len(entries)==2 and {
        (entry.get('platform',{}).get('os'),entry.get('platform',{}).get('architecture'),entry.get('digest'))
        for entry in entries
    }=={('linux',arch,digest) for arch,digest in digests.items()}

def inspect_manifest(tag):
    return json.loads(subprocess.check_output(['docker','buildx','imagetools','inspect','--raw',tag],text=True))

def merge(directory,release):
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    plan=publication_plan(directory,release,revision,root=ROOT)
    # Inspect all existing release tags before changing any of them. A retry may
    # resume identical manifests; a different manifest must never be overwritten.
    existing=set(registry_tags(release.split('-')[0]))
    ready=set()
    for major,digests in plan.items():
        tag=release_tag(major,release)
        if tag.rsplit(':',1)[1] in existing:
            require(matches_manifest(inspect_manifest(tag),digests),f'Release tag already contains different images: {tag}')
            ready.add(major)
    lines=[]
    for major,digests in plan.items():
        tag=release_tag(major,release)
        if major not in ready:
            run(['docker','buildx','imagetools','create','--tag',tag,
                 *[REPOSITORY+'@'+digests[arch] for arch in ARCHES]])
        require(matches_manifest(inspect_manifest(tag),digests),f'Published manifest verification failed: {tag}')
        lines.append(f'- `{tag}` — linux/amd64, linux/arm64')
        print('Published and verified:',tag,flush=True)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as stream:
            stream.write('## Docker Hub release '+release+'\n\n'+'\n'.join(lines)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest='command',required=True)
    native=sub.add_parser('stage');native.add_argument('--variant',choices=VARIANTS,required=True);native.add_argument('--arch',choices=ARCHES,required=True)
    final=sub.add_parser('merge');final.add_argument('--directory',type=Path,required=True)
    args=parser.parse_args();release=validate(os.environ['PLATFORM_VERSION'])
    if args.command=='stage':stage(args.variant,args.arch,release)
    else:merge(args.directory,release)
