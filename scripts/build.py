"""Build and validate native images with exact identity and dependency reports."""
import argparse
from datetime import datetime, timezone
import json
import hashlib
import os
from pathlib import Path
import platform
import subprocess
import uuid
from common import ROOT, matrix, cli, config, image, run, write_json, read_json
from render import render
from version import select, validate as validate_version

def logged(args,path):
    print('+', ' '.join(map(str,args)), '->', path, flush=True)
    with path.open('w') as out:
        try:
            subprocess.run(list(map(str,args)),cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,check=True)
        except subprocess.CalledProcessError:
            out.flush()
            print(''.join(path.read_text().splitlines(keepends=True)[-80:]),flush=True)
            raise

def outcome(path):
    for line in reversed(path.read_text().splitlines()):
        if line.startswith('{'):
            try:value=json.loads(line)
            except json.JSONDecodeError:continue
            if value.get('outcome')=='success':return value
    raise RuntimeError(f'No successful devcontainer result in {path}')

def validate(major,report_dir):
    data=matrix();variant=data['variants'][major]
    tag=image(major)
    expected=os.environ['PLATFORM_VERSION']
    actual=subprocess.check_output(['docker','run','--rm',tag,'cat','/etc/platform_version'],text=True).strip()
    inspected=json.loads(subprocess.check_output(['docker','image','inspect',tag]))[0]['Config']
    assert actual==expected
    assert f'PLATFORM_VERSION={expected}' in inspected['Env']
    assert inspected['Labels']['org.opencontainers.image.version']==expected
    tests=ROOT/'.devcontainer/tests'
    # Audit the pristine image before running user tools that may create runtime caches.
    for script in ['caches.py','no-version-managers.py']:
        run(['docker','run','--rm','-v',f'{tests}:/tests:ro',tag,'python','/tests/'+script])
    # Verify every transitive lock pin in the actual image, not only pip's consistency check.
    run(['docker','run','--rm','-v',f'{ROOT}:/repo:ro',tag,'python','/repo/.devcontainer/tests/lock.py',major])
    for feature in ['node','gilt','cli-tools']:
        run(['docker','run','--rm','-e',f'GILT_VERSION={data["tools"]["gilt"]}',
             '-v',f'{tests}:/tests:ro','-v',f'{ROOT}/.devcontainer/features/{feature}:/feature:ro',tag,'bash',f'/tests/{feature}.sh'])
    label='ansible.matrix.validation';token=uuid.uuid4().hex
    up_log=report_dir/f'up-{major}.log'
    container=None
    try:
        logged([cli(),'up','--workspace-folder',ROOT,'--config',config(major),'--id-label',f'{label}={token}'],up_log)
        result=outcome(up_log);container=result['containerId'];workspace=result['remoteWorkspaceFolder']
        inspected=json.loads(subprocess.check_output(['docker','inspect',container]))[0]
        assert inspected['Config']['Labels'].get(label)==token
        for name,command in [('smoke',['sh',workspace+'/.devcontainer/tests/smoke.sh']),('gilt',['bash',workspace+'/.devcontainer/tests/gilt-overlay.sh']),('host-docker',['docker','info','--format','{{.ServerVersion}}']),('molecule',['sh',workspace+'/.devcontainer/tests/molecule.sh'])]:
            args=['docker','exec','--user','vscode','--workdir','/tmp','-e',f'ANSIBLE_MAJOR={major}',
                  '-e',f'MOLECULE_TARGET_IMAGE={variant["pythonImage"]}','-e',f'MOLECULE_TEST_ID={token}',container,*command]
            logged(args,report_dir/f'{name}-{major}.log')
            print(f'PASS: Ansible {major} {name}',flush=True)
    finally:
        # Only our uniquely labelled validation container may be removed.
        owned=subprocess.check_output(['docker','ps','-aq','--filter',f'label={label}={token}'],text=True).split()
        for item in owned:run(['docker','rm','--force',item])

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--variants',nargs='+',choices=['10','12','14'],default=['10','12','14'])
    parser.add_argument('--test',action='store_true')
    parser.add_argument('--test-only',action='store_true')
    parser.add_argument('--no-cache',action='store_true',help='Refresh apt and build dependencies for a release update.')
    parser.add_argument('--platform',default='linux/arm64' if platform.machine() in ['aarch64','arm64'] else 'linux/amd64')
    args=parser.parse_args();render(check=True)
    arch=args.platform.split('/')[-1]
    if (arch=='arm64') != (platform.machine() in ['arm64','aarch64']) and (args.test or args.test_only):
        raise SystemExit('Full tests require a native runner; use the matching architecture CI matrix job.')
    folder=ROOT/'.build'/arch;folder.mkdir(parents=True,exist_ok=True)
    data=matrix()
    if not os.environ.get('PLATFORM_VERSION'):
        if args.test_only:raise SystemExit('Set PLATFORM_VERSION to the existing dated release for --test-only')
        os.environ['PLATFORM_VERSION']=select()
    validate_version(os.environ['PLATFORM_VERSION'])
    print('Release:',os.environ['PLATFORM_VERSION'],flush=True)
    old=folder/'results.json'
    results=read_json(old)['images'] if old.exists() else {}
    for major in args.variants:
        if not args.test_only:
            path=folder/f'build-{major}.log'
            command=[cli(),'build','--workspace-folder',ROOT,'--config',config(major),'--image-name',image(major),'--platform',args.platform,'--frozen-lockfile']
            if args.no_cache:command.append('--no-cache')
            logged(command,path)
            outcome(path)
        inspected=json.loads(subprocess.check_output(['docker','image','inspect',image(major)]))[0]
        size=inspected['Size']
        limit=data['variants'][major]['maxImageBytes']
        if size>limit:raise SystemExit(f'Ansible {major}: image {size} bytes exceeds reviewed budget {limit}')
        results[major]={'image':image(major),'bytes':size,'budgetBytes':limit,'platform':args.platform,'tested':False,
                        'pythonImage':data['variants'][major]['pythonImage'],'platformVersion':os.environ['PLATFORM_VERSION'],'imageId':inspected['Id'],
                        'manifestSha256':hashlib.sha256((ROOT/'images.json').read_bytes()).hexdigest(),
                        'lockSha256':hashlib.sha256((ROOT/f'requirements/ansible{major}.txt').read_bytes()).hexdigest()}
        write_json(folder/'results.json',{'date':datetime.now(timezone.utc).isoformat(),'images':results})
        if args.test or args.test_only:
            validate(major,folder);results[major]['tested']=True
            write_json(folder/'results.json',{'date':datetime.now(timezone.utc).isoformat(),'images':results})
        print(f'PASS: Ansible {major}; {size:,} bytes',flush=True)

if __name__=='__main__':main()
