"""Check the installed Python environment against every committed lock pin."""
from importlib.metadata import version
import json
from pathlib import Path
import re
import sys
import subprocess

root=Path('/repo')
major=sys.argv[1]
manifest=json.loads((root/'images.json').read_text())
data=manifest['variants'][major]
assert '.'.join(map(str,sys.version_info[:2]))==data['pythonMinor']
pins=dict(re.findall(r'^([\w.-]+)==([^\s\\]+)',(root/f'requirements/ansible{major}.txt').read_text(),re.M))
assert version('ansible').startswith(major+'.')
assert version('ansible-core').startswith(data['coreMinor']+'.')
for name,expected in pins.items():
    assert version(name)==expected,(name,version(name),expected)
output=lambda command:subprocess.check_output(command,text=True).strip()
assert output(['node','--version'])=='v'+manifest['tools']['node']['version']
assert output(['npm','--version'])==manifest['tools']['node']['npmVersion']
assert output(['git','--version'])=='git version '+manifest['tools']['git']['version']
assert output(['dpkg-query','-W','-f=${Version}','git'])=='1:'+manifest['tools']['git']['version']
assert output(['claude','--version']).split()[0]==manifest['tools']['cliTools']['claudeVersion']
print(f'PASS: Python {sys.version.split()[0]} and all {len(pins)} locked distributions for Ansible {major}')

k9s_version=re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',output(['k9s','version','--short']))
assert re.search(r'(?im)^\s*(?:Version\s*:?\s*)?v?'+re.escape(manifest['tools']['k9s'])+r'(?:\s|$)',k9s_version),k9s_version
