#!/usr/bin/env bash
# Sourced while the checksum-pinned temporary Go toolchain is active.
set -euo pipefail
make_literal_version() {
    local name="${1:?Makefile variable}" file="${2:?Makefile path}" value definition
    local -a definitions
    [[ "$name" =~ ^[A-Z][A-Z0-9_]*$ ]] || return 1
    mapfile -t definitions < <(sed -nE "s/^[[:space:]]*((export|override|private)[[:space:]]+)*${name}[[:space:]]*([:?+!]*=)[[:space:]]*(.*)$/\3|\4/p" "$file")
    if [ "${#definitions[@]}" -ne 1 ]; then
        echo "Review minikube Makefile variable $name: expected one assignment." >&2
        return 1
    fi
    definition="${definitions[0]}"
    case "${definition%%|*}" in
        '='|':='|'?=') ;;
        *) echo "Review minikube Makefile assignment operator for $name." >&2; return 1 ;;
    esac
    value="${definition#*|}"
    value="${value%%#*}"
    value="$(sed -E 's/^[[:space:]]+//;s/[[:space:]]+$//' <<< "$value")"
    if [[ ! "$value" =~ ^v[0-9]+(\.[0-9]+)*(-[0-9A-Za-z.-]+)?$ ]]; then
        echo "Review minikube Makefile variable $name: expected one literal version." >&2
        return 1
    fi
    printf '%s\n' "$value"
}
build_extra_go_tools() {
local feature_dir="${1:?feature directory}" work_dir="${2:?temporary build directory}"
export GOWORK=off GOSUMDB=sum.golang.org
while IFS= read -r tool_json; do
    tool_name="$(jq -r .key <<< "$tool_json")"
    export CGO_ENABLED=0 GOFLAGS='-p=2 -mod=mod -trimpath'
    if [ "$tool_name" = minikube ]; then
        # Upstream Linux build: retain KVM support without linking libvirt.so.
        export CGO_ENABLED=1 GOFLAGS="$GOFLAGS -tags=libvirt_dlopen"
    fi
    tool_version="$(jq -r .value.version <<< "$tool_json")"
    tool_digest="$(jq -r .value.sha256 <<< "$tool_json")"
    tool_url="$(jq -r .value.url <<< "$tool_json")"
    tool_folder="$work_dir/extra-$tool_name"
    mkdir "$tool_folder"
    if [ "$tool_name" = kubectl ]; then
        download "$tool_url" "$tool_folder/main.go"
        echo "$tool_digest  $tool_folder/main.go" | sha256sum --check
        cd "$tool_folder"
        go mod init ansible-infra.build/kubectl
        kube_module_version="v0.${tool_version#*.}"
        go get "k8s.io/kubectl@$kube_module_version" "k8s.io/component-base@$kube_module_version" "k8s.io/client-go@$kube_module_version"
        tool_package=.
    else
        download "$tool_url" "$work_dir/$tool_name.tar.gz"
        echo "$tool_digest  $work_dir/$tool_name.tar.gz" | sha256sum --check
        tar -xzf "$work_dir/$tool_name.tar.gz" -C "$tool_folder" --strip-components=1 --no-same-owner
        cd "$tool_folder"
        tool_package="$(jq -r .value.package <<< "$tool_json")"
    fi
    mapfile -t patched_modules < <(jq -r '.value.modules | to_entries[] | .key+"@"+.value' <<< "$tool_json")
    if [ "$tool_name" != kubectl ]; then source_epoch="$(stat -c %Y go.mod)"; fi
    go get "${patched_modules[@]}"
    go mod verify
    if [ "$tool_name" = kubectl ]; then
        build_date="$(go list -m -json k8s.io/kubectl | jq -r .Time)"
    else
        build_date="$(date -u -d "@$source_epoch" +%Y-%m-%dT%H:%M:%SZ)"
    fi
    case "$tool_name" in
        k9s)
            go test ./internal/config/... ./cmd/...
            tool_ldflags="-s -w -X github.com/derailed/k9s/cmd.version=v$tool_version -X github.com/derailed/k9s/cmd.date=$build_date"
            ;;
        minikube)
            go test ./pkg/minikube/config/...
            iso_version="$(make_literal_version ISO_VERSION Makefile)"
            storage_version="$(make_literal_version STORAGE_PROVISIONER_TAG Makefile)"
            tool_ldflags="-s -w -X k8s.io/minikube/pkg/version.version=v$tool_version -X k8s.io/minikube/pkg/version.isoVersion=$iso_version -X k8s.io/minikube/pkg/version.storageProvisionerVersion=$storage_version"
            ;;
        kubectl)
            tool_ldflags="-s -w -X k8s.io/client-go/pkg/version.gitVersion=v$tool_version -X k8s.io/component-base/version.gitVersion=v$tool_version -X k8s.io/client-go/pkg/version.gitMajor=${tool_version%%.*} -X k8s.io/client-go/pkg/version.gitMinor=$(cut -d. -f2 <<< "$tool_version") -X k8s.io/component-base/version.buildDate=$build_date -X k8s.io/client-go/pkg/version.buildDate=$build_date"
            ;;
        *) exit 1 ;;
    esac
    go build -trimpath -ldflags "$tool_ldflags" -o "$work_dir/$tool_name" "$tool_package"
    install -m 0755 "$work_dir/$tool_name" "/usr/local/bin/$tool_name"
    mkdir -p "/usr/local/share/go-clis/$tool_name"
    cp go.mod go.sum "/usr/local/share/go-clis/$tool_name/"
    go list -deps -f '{{.ImportPath}}' "$tool_package" > "/usr/local/share/go-clis/$tool_name/packages.txt"
    printf '%s\n' "$tool_version" > "/usr/local/share/go-clis/$tool_name/version"
    for license_name in LICENSE LICENSE.md LICENCE; do
        if [ -f "$license_name" ]; then cp "$license_name" "/usr/local/share/go-clis/$tool_name/"; break; fi
    done
done < <(jq -c '.projects | to_entries[]' "$feature_dir/go-tools.json")
}
