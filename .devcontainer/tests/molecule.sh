#!/bin/sh
set -eu
mkdir -p /tmp/molecule-smoke/molecule/default
cd /tmp/molecule-smoke
cat > molecule/default/molecule.yml <<'YAML'
---
dependency:
  name: galaxy
  enabled: false
driver:
  name: docker
platforms:
  - name: ansible10-molecule-py312
    image: python:3.12.16-slim-trixie
    pre_build_image: true
    command: sleep infinity
YAML
# Python 3.7 is an optional external managed-node compatibility test.
if [ "${TEST_LEGACY_PYTHON:-0}" = 1 ]; then
cat >> molecule/default/molecule.yml <<'YAML'
  - name: ansible10-molecule-py37
    image: python:3.7-slim-bullseye
    pre_build_image: true
    command: sleep infinity
YAML
fi
cat >> molecule/default/molecule.yml <<'YAML'
provisioner:
  name: ansible
  inventory:
    group_vars:
      all:
        ansible_python_interpreter: /usr/local/bin/python
verifier:
  name: ansible
scenario:
  destroy_sequence:
    - destroy
  test_sequence:
    - destroy
    - create
    - converge
    - idempotence
    - verify
    - destroy
YAML
cat > molecule/default/converge.yml <<'YAML'
---
- name: Converge
  hosts: all
  gather_facts: false
  tasks:
    - name: Write verification file
      ansible.builtin.copy:
        content: ansible10 works
        dest: /tmp/ansible10-smoke
        mode: '0644'
YAML
cat > molecule/default/verify.yml <<'YAML'
---
- name: Verify
  hosts: all
  gather_facts: true
  tasks:
    - name: Check managed Python compatibility
      ansible.builtin.assert:
        that:
          - ansible_facts.python.version.major == 3
          - ansible_facts.python.version.minor in [7, 12]
    - name: Read verification file
      ansible.builtin.slurp:
        src: /tmp/ansible10-smoke
      register: smoke_file
    - name: Check verification file
      ansible.builtin.assert:
        that:
          - smoke_file.content | b64decode == 'ansible10 works'
YAML
trap 'molecule destroy' EXIT
molecule test
