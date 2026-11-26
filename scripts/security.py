"""Scan the exact tested image; retain all findings and apply narrow accepted risks."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from publish import checked_result
from common import ROOT, matrix, write_json

ACCEPTED={
    ('10','python-pkg','ansible','CVE-2025-14010'):'Ansible 10 compatibility explicitly required by the repository owner.',
    ('10','python-pkg','ansible-core','CVE-2026-11332'):'Ansible 10/core 2.17 compatibility explicitly required by the repository owner.',
}

def evaluate(report,variant):
    if report.get('SchemaVersion')!=2 or not isinstance(report.get('Results'),list) or not report['Results']:
        raise ValueError('Missing or invalid Trivy results')
    if not any(row.get('Type')=='debian' for row in report['Results']):
        raise ValueError('Missing Debian OS vulnerability scan')
    result={'variant':variant,'findings':[],'accepted':[],'blocked':[]}
    for target in report['Results']:
        for item in target.get('Vulnerabilities') or []:
            row={key:item.get(key) for key in ('VulnerabilityID','PkgName','InstalledVersion','FixedVersion','Severity','Status','PrimaryURL')}
            row.update(target=target['Target'],type=target.get('Type'))
            reason=ACCEPTED.get((variant,target.get('Type'),item['PkgName'],item['VulnerabilityID']))
            family={'ansible':'10.','ansible-core':'2.17.'}.get(item['PkgName'])
            if reason and not item['InstalledVersion'].startswith(family):reason=None
            if reason:
                row['acceptedReason']=reason;result['accepted'].append(row)
            elif item['Severity'] in ('HIGH','CRITICAL'):
                result['blocked'].append(row)
            result['findings'].append(row)
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--variant',required=True,choices=['10','12','14'])
    parser.add_argument('--arch',required=True,choices=['amd64','arm64'])
    parser.add_argument('--report',help='Evaluate an existing Trivy JSON report without rescanning')
    args=parser.parse_args()
    folder=ROOT/'.build'/args.arch;folder.mkdir(parents=True,exist_ok=True)
    raw=folder/f'trivy-{args.variant}.json'
    image_id=None
    if args.report:
        report=json.loads(Path(args.report).read_text())
        write_json(raw,report)
    else:
        release=json.loads((folder/'results.json').read_text())['images'][args.variant]['platformVersion']
        record=checked_result(args.variant,args.arch,release)
        image_id=record['imageId']
        actual=json.loads(subprocess.check_output(['docker','image','inspect',record['image']]))[0]['Id']
        if actual!=image_id:raise ValueError('Tested image has changed')
        scanner=matrix()['security']['trivyImage']
        cache=ROOT/'.build/trivy-cache';cache.mkdir(exist_ok=True)
        command=['docker','run','--rm','-v','/var/run/docker.sock:/var/run/docker.sock',
                 '-v',f'{folder}:/reports','-v',f'{cache}:/cache','-e','TRIVY_CACHE_DIR=/cache',scanner]
        subprocess.run([*command,'image','--image-src','docker','--scanners','vuln','--list-all-pkgs',
                        '--format','json','--output',f'/reports/{raw.name}',image_id],check=True)
        subprocess.run([*command,'convert','--format','cyclonedx','--output',f'/reports/sbom-{args.variant}.cdx.json',f'/reports/{raw.name}'],check=True)
        report=json.loads(raw.read_text())
    result=evaluate(report,args.variant)
    result.update(imageId=image_id,policySha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),trivyImage=matrix()['security']['trivyImage'],reportSha256=hashlib.sha256(raw.read_bytes()).hexdigest())
    write_json(folder/f'security-{args.variant}.json',result)
    print(f"Security: {len(result['blocked'])} blocked High/Critical, {len(result['accepted'])} explicitly accepted; full report: {raw}")
    if result['blocked']:raise SystemExit(1)

if __name__=='__main__':main()
