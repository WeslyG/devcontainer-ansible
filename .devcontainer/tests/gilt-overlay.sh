#!/usr/bin/env bash
set -euo pipefail
work_dir="$(mktemp -d)"
trap 'rm -rf -- "$work_dir"' EXIT
git init -q "$work_dir/origin"
git -C "$work_dir/origin" config user.name "Gilt test"
git -C "$work_dir/origin" config user.email "gilt-test@example.invalid"
printf 'Gilt overlay works\n' > "$work_dir/origin/payload.txt"
git -C "$work_dir/origin" add payload.txt
git -C "$work_dir/origin" commit -qm "Test fixture"
revision="$(git -C "$work_dir/origin" rev-parse HEAD)"
cat > "$work_dir/Giltfile.yaml" <<YAML
repositories:
  - git: file://$work_dir/origin
    version: $revision
    dstdir: $work_dir/destination
YAML
gilt --gilt-dir "$work_dir/cache" --gilt-file "$work_dir/Giltfile.yaml" overlay
cmp "$work_dir/origin/payload.txt" "$work_dir/destination/payload.txt"
echo "PASS: Gilt overlays a local repository pinned to a commit"
