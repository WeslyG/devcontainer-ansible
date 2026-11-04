#!/bin/sh
set -eu
work_dir="$(mktemp -d)"
mkdir -p "$work_dir/molecule/default"
cd "$work_dir"
cat > molecule/default/molecule.yml <<YAML
---
dependency:
  name: galaxy
  enabled: false
driver:
  name: docker
platforms:
  - name: ansible${ANSIBLE_MAJOR}-molecule-${MOLECULE_TEST_ID:-local}
    image: ${MOLECULE_TARGET_IMAGE:?Set a supported target image}
    pre_build_image: true
    command: sleep infinity
YAML
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
        content: ansible works
        dest: /tmp/ansible-smoke
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
          - ansible_facts.python.version.minor >= 9
    - name: Read verification file
      ansible.builtin.slurp:
        src: /tmp/ansible-smoke
      register: smoke_file
    - name: Check verification file
      ansible.builtin.assert:
        that:
          - smoke_file.content | b64decode == 'ansible works'
YAML
trap 'molecule destroy; rm -rf -- "$work_dir"' EXIT
molecule test
