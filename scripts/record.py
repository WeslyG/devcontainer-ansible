"""Explicitly copy successful local measurements into the reviewed compatibility record."""
import argparse
import hashlib
from common import ROOT, read_json, write_json, matrix

parser=argparse.ArgumentParser();parser.add_argument('--arch',default='amd64');args=parser.parse_args()
result=read_json(ROOT/f'.build/{args.arch}/results.json')
assert set(result['images'])=={'10','12','14'}
assert all(r['tested'] for r in result['images'].values())
from version import validate
assert len({validate(row['platformVersion']) for row in result['images'].values()})==1, 'Record one complete release matrix'
for major,value in result['images'].items():
    assert value['image']==f'ansible-infra:ansible{major}-{value["platformVersion"]}'
    assert value['manifestSha256']==hashlib.sha256((ROOT/'images.json').read_bytes()).hexdigest()
    assert value['pythonImage']==matrix()['variants'][major]['pythonImage']
    assert value['lockSha256']==hashlib.sha256((ROOT/f'requirements/ansible{major}.txt').read_bytes()).hexdigest()
path=ROOT/'compatibility/validation.json'
data=read_json(path) if path.exists() else {}
data[args.arch]=result
write_json(path,data)
from render import render
render()
