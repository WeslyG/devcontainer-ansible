#!/bin/sh
set -eu
python --version
python -m pip check
python "$(dirname "$0")/no-version-managers.py"
black --version
isort --version-number
s3cmd --version
yq --version
test "$(printf 'answer: 42\n' | yq -r ' .answer')" = 42
docker compose version
docker buildx version
ansible --version
ansible-lint --version
molecule --version
molecule drivers
node --version
npm --version
kubectl version --client
helm version --short
minikube version --short
k9s version --short
elasticdump --version
docker --version
claude --version
cookiecutter --version
gilt version
yamllint --version
pylint --version
python - <<'PY'
import importlib
from importlib.metadata import distributions, version
for module in ['netaddr','dns','docker','testinfra','kubernetes','yaml','jsonpatch','hvac','pytz','pynetbox','pydantic','cookiecutter','ruamel.yaml']:
    importlib.import_module(module)
import os
major=os.environ['ANSIBLE_MAJOR']
core={'10':'2.17.','12':'2.19.','14':'2.21.'}[major]
assert version('ansible').startswith(major+'.')
assert version('ansible-core').startswith(core)
import sys
from pathlib import Path
assert sys.version_info[:2] == {'10':(3,12),'12':(3,13),'14':(3,14)}[major]
assert not Path('/usr/bin/python3').exists(), 'Unexpected second/system Python'
assert not Path('/usr/local/py-utils').exists(), 'Unexpected duplicate tool environments'
assert not Path('/usr/bin/dockerd').exists(), 'Docker daemon must stay on the host'
assert not Path('/usr/bin/gcc').exists(), 'Build compiler must stay in the builder stage'
assert Path('/usr/local/bin/claude').is_symlink(), 'Claude must not have a second binary copy'
native=Path.home()/'.local/share/claude/versions'
assert native.parent.stat().st_uid==os.getuid(), 'Native Claude layout must belong to vscode'
assert len(list(native.iterdir()))==1, 'Keep only one native Claude release'
assert Path('/usr/local/bin/claude').resolve().parent==native.resolve()
assert not Path('/usr/local/lib/node_modules/@anthropic-ai/claude-code').exists(), 'Do not duplicate the native CLI with an npm wrapper'
assert not any(d.metadata['Name'].lower().replace('_', '-') == 'python-gilt' for d in distributions())
from passlib.hash import bcrypt
h=bcrypt.hash('smoke-test')
assert bcrypt.verify('smoke-test',h)
from ansible.parsing.vault import VaultLib, VaultSecret
vault = VaultLib([('default', VaultSecret(b'public-smoke-test-secret'))])
assert vault.decrypt(vault.encrypt(b'ansible-vault-test')) == b'ansible-vault-test'
import magic
assert magic.from_buffer(b'plain text payload\n'*8,mime=True).startswith('text/')
import testinfra
host=testinfra.get_host('local://')
assert host.file('/usr/local/bin/python').exists
assert host.run('python --version').rc==0
print('Python imports, bcrypt, Vault, libmagic and Testinfra local backend OK')
PY
mkdir -p /tmp/ansible-smoke
cat > /tmp/ansible-smoke/playbook.yml <<'YAML'
---
- name: Verify local Ansible execution
  hosts: localhost
  gather_facts: true
  tasks:
    - name: Check Python and bcrypt filter
      ansible.builtin.assert:
        that:
          - ansible_facts.python.version.major == 3
          - "('smoke-test' | ansible.builtin.password_hash('bcrypt')) is match('^[$]2')"
    - name: Run a local command
      ansible.builtin.command: /bin/true
      changed_when: false
YAML
cd /tmp/ansible-smoke
ansible-lint playbook.yml
ansible-playbook -i localhost, -c local playbook.yml
