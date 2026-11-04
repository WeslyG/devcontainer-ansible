"""Compare every selected package with PyPI's current stable release."""
import argparse
import concurrent.futures
from common import ROOT, fetch, matrix, read_json, write_json

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
    data=read_json(ROOT/'compatibility/resolved.json')
    names=sorted(set().union(*(set(x) for x in data['packages'].values())))
    def latest(name):return name,fetch(f'https://pypi.org/pypi/{name}/json')['info']['version']
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:versions=dict(pool.map(latest,names))
    rows={}
    for major,packages in data['packages'].items():
        rows[major]={}
        for name,selected in packages.items():
            reason='latest stable'
            if selected!=versions[name]:
                reason='resolver selected a version compatible with the full environment; see .build/resolve-'+major+'.json'
                if name in ['ansible','ansible-core']:reason='pinned Ansible major / supported core family'
                if name=='bcrypt':reason='passlib 1.7.4 rejects bcrypt 5 (long-password backend probe); runtime roundtrip tested'
            rows[major][name]={'selected':selected,'latest':versions[name],'reason':reason}
    target=ROOT/('compatibility/packages.json' if args.write else '.build/package-audit.json')
    write_json(target,{'updatedAt':matrix()['updatedAt'],'variants':rows})
    print('Package audit:',target)

if __name__=='__main__':main()
