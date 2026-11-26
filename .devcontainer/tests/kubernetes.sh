#!/usr/bin/env bash
set -euo pipefail
feature_dir="${FEATURE_DIR:-/feature}"
eval "$(python - "$feature_dir/devcontainer-feature.json" <<'PY'
import json,shlex,sys
for key,item in json.load(open(sys.argv[1]))['options'].items():print('export '+key.upper()+'='+shlex.quote(item['default']))
PY
)"
kubectl version --client -o json | python -c 'import json,os,sys; assert json.load(sys.stdin)["clientVersion"]["gitVersion"]=="v"+os.environ["VERSION"]'
[[ "$(helm version --short)" == "v$HELM"* ]]
test "$(minikube version --short)" = "v$MINIKUBE"
work_dir="$(mktemp -d)"
trap 'rm -rf -- "$work_dir"' EXIT
before="$(sha256sum /usr/local/bin/kubectl /usr/local/bin/helm /usr/local/bin/minikube)"
mkdir "$work_dir/bin"
cat > "$work_dir/bin/curl" <<'SH'
#!/bin/sh
while [ "$#" -gt 0 ]; do
    if [ "$1" = --output ]; then printf 'corrupted archive' > "$2"; exit 0; fi
    shift
done
exit 1
SH
chmod +x "$work_dir/bin/curl"
if PATH="$work_dir/bin:$PATH" bash "$feature_dir/install.sh" > "$work_dir/corrupt.log" 2>&1; then
    echo 'ERROR: accepted a corrupt Kubernetes binary' >&2; exit 1
fi
grep -q 'did NOT match' "$work_dir/corrupt.log"
test "$(sha256sum /usr/local/bin/kubectl /usr/local/bin/helm /usr/local/bin/minikube)" = "$before"
if VERSION=latest bash "$feature_dir/install.sh" > "$work_dir/version.log" 2>&1; then exit 1; fi
grep -q 'Specify exact' "$work_dir/version.log"
echo 'PASS: Kubernetes versions and integrity guards'

# Source minikube uses the upstream libvirt_dlopen build tag.
dependencies="$(ldd /usr/local/bin/minikube)"
if grep -Eq 'not found|libvirt[.]so' <<< "$dependencies"; then
    echo 'ERROR: minikube has missing or mandatory libvirt shared dependencies' >&2
    exit 1
fi
minikube start --help > /dev/null
echo 'PASS: minikube Linux runtime links resolve without mandatory libvirt.so'
