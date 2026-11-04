"""Offline repository invariants shared by contributors and CI."""
import json
from pathlib import Path
import re
from common import ROOT, matrix, config
from render import render

def check():
    render(check=True)
    data=matrix()
    assert set(data['variants'])=={'10','12','14'}
    for major,variant in data['variants'].items():
        assert '@sha256:' in variant['pythonImage']
        text=(ROOT/f'requirements/ansible{major}.txt').read_text()
        pins=dict(re.findall(r'^([\w.-]+)==([^\s\\]+)',text,re.M))
        assert pins['ansible'].startswith(major+'.')
        assert pins['ansible-core'].startswith(variant['coreMinor']+'.')
        assert '--hash=sha256:' in text
        assert int(pins['bcrypt'].split('.')[0])<5
        lock=json.loads((config(major).parent/'devcontainer-lock.json').read_text())
        assert not any('features/node:' in name or 'features/python:' in name for name in lock['features'])
    assert {p.name for p in (ROOT/'.github/workflows').glob('*.yml')}=={'build.yml','update.yml'}
    for path in (ROOT/'.github/workflows').glob('*.yml'):
        workflow=path.read_text()
        assert '--push' not in workflow and 'login-action' not in workflow
        assert 'contents: read' in workflow
        assert 'include-hidden-files: true' not in workflow
        assert 'scripts/artifacts.py' in workflow
        assert 'path: artifacts/\n' not in workflow
    print('PASS: generated configs, all core families/hash locks, feature locks and build-only CI')

if __name__=='__main__':check()
