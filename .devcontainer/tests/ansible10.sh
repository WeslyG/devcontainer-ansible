#!/bin/sh
set -eu
python --version
python -m pip check
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
assert version('ansible').startswith('10.')
assert version('ansible-core').startswith('2.17.')
import sys
assert sys.version_info[:2] == (3, 12)
assert not any(d.metadata['Name'].lower().replace('_', '-') == 'python-gilt' for d in distributions())
from passlib.hash import bcrypt
h=bcrypt.hash('smoke-test')
assert bcrypt.verify('smoke-test',h)
from ansible.parsing.vault import VaultLib, VaultSecret
vault = VaultLib([('default', VaultSecret(b'public-smoke-test-secret'))])
assert vault.decrypt(vault.encrypt(b'ansible10-vault-test')) == b'ansible10-vault-test'
print('Python imports, bcrypt and Ansible Vault roundtrips OK')
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
