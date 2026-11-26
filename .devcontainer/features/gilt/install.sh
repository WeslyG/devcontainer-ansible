#!/usr/bin/env bash
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then echo 'Gilt feature must be installed as root.' >&2; exit 1; fi
version="${VERSION:-2.2.5}"
version="${version#v}"
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo 'Specify an exact Gilt release version.' >&2; exit 1
fi
go_version="${GOVERSION:?Set an exact build Go version}"
source_digest="${SOURCESHA256:?Set the Gilt source SHA256}"
case "$(uname -m)" in
    x86_64|amd64) architecture=amd64; go_digest="${GOSHA256AMD64:?}" ;;
    aarch64|arm64) architecture=arm64; go_digest="${GOSHA256ARM64:?}" ;;
    *) echo 'Unsupported Gilt architecture' >&2; exit 1 ;;
esac
feature_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
extra_sha="$(sha256sum "$feature_dir/build-extras.sh" "$feature_dir/go-tools.json" "$feature_dir/source-sbom.cdx.json" | cut -d' ' -f1 | sha256sum | cut -d' ' -f1)"
pins_sha="$(printf '%s\n' "$version" "$go_version" "$GOSHA256AMD64" "$GOSHA256ARM64" "$source_digest" "$CRYPTOVERSION" "$TEXTVERSION" "$EDITORCONFIGVERSION" "$EDITORCONFIGSOURCESHA256" "$extra_sha" "$(sha256sum "${BASH_SOURCE[0]}" | cut -d' ' -f1)" | sha256sum | cut -d' ' -f1)"
if [ -f /usr/local/share/go-clis/pins.sha256 ] && [ "$(cat /usr/local/share/go-clis/pins.sha256)" = "$pins_sha" ]; then
    sha256sum --check /usr/local/share/go-clis/binaries.sha256
    gilt version
    ec --version
    k9s version --short
    kubectl version --client
    minikube version --short
    exit 0
fi
work_dir="$(mktemp -d)"
trap 'rm -rf -- "$work_dir"' EXIT
download() {
    local separator='?'
    [[ "$1" != *'?'* ]] || separator='&'
    curl --fail --silent --show-error --location --retry 2 --connect-timeout 15 --max-time 240 "$1${separator}ansible-transfer=${RANDOM}${RANDOM}" --output "$2"
}
download "https://codeload.github.com/retr0h/gilt/tar.gz/refs/tags/v${version}" "$work_dir/source.tar.gz"
echo "$source_digest  $work_dir/source.tar.gz" | sha256sum --check
download "https://dl.google.com/go/go${go_version}.linux-${architecture}.tar.gz?ansible-infra=1" "$work_dir/go.tar.gz"
echo "$go_digest  $work_dir/go.tar.gz" | sha256sum --check
mkdir "$work_dir/source"
tar -xzf "$work_dir/source.tar.gz" -C "$work_dir/source" --strip-components=1 --no-same-owner
tar -xzf "$work_dir/go.tar.gz" -C "$work_dir" --no-same-owner
export PATH="$work_dir/go/bin:$PATH" GOTOOLCHAIN=local CGO_ENABLED=0
export GOPATH="$work_dir/gopath" GOCACHE="${GO_BUILD_CACHE:-$work_dir/cache}" GOMAXPROCS=2
export GOFLAGS='-p=2 -trimpath'
cd "$work_dir/source"
go get "golang.org/x/crypto@${CRYPTOVERSION:?}" "golang.org/x/text@${TEXTVERSION:?}"
go mod verify
go test ./...
go build -trimpath -ldflags "-s -w -X github.com/retr0h/gilt/v2/cmd.version=$version -X github.com/retr0h/gilt/v2/cmd.builtBy=ansible-infra" -o "$work_dir/gilt" .
"$work_dir/gilt" version
go version -m "$work_dir/gilt"
install -m 0755 "$work_dir/gilt" /usr/local/bin/gilt
mkdir -p /usr/local/share/gilt
cp go.mod go.sum LICENSE /usr/local/share/gilt/

editorconfig_version="${EDITORCONFIGVERSION:?}"
download "https://codeload.github.com/editorconfig-checker/editorconfig-checker/tar.gz/refs/tags/v${editorconfig_version}" "$work_dir/editorconfig.tar.gz"
echo "${EDITORCONFIGSOURCESHA256:?}  $work_dir/editorconfig.tar.gz" | sha256sum --check
mkdir "$work_dir/editorconfig"
tar -xzf "$work_dir/editorconfig.tar.gz" -C "$work_dir/editorconfig" --strip-components=1 --no-same-owner
cd "$work_dir/editorconfig"
go get "golang.org/x/text@${TEXTVERSION}"
go mod verify
go test ./...
go build -trimpath -ldflags '-s -w' -o "$work_dir/ec" ./cmd/editorconfig-checker
"$work_dir/ec" --version
install -m 0755 "$work_dir/ec" /usr/local/bin/ec
ln -sfn ec /usr/local/bin/editorconfig-checker
mkdir -p /usr/local/share/editorconfig-checker
cp go.mod go.sum LICENSE /usr/local/share/editorconfig-checker/

# shellcheck source=build-extras.sh
source "$feature_dir/build-extras.sh"
build_extra_go_tools "$feature_dir" "$work_dir"
mkdir -p /usr/local/share/go-clis
cp "$feature_dir/source-sbom.cdx.json" /usr/local/share/go-clis/source-sbom.cdx.json
printf '%s\n' "$pins_sha" > /usr/local/share/go-clis/pins.sha256
sha256sum /usr/local/bin/gilt /usr/local/bin/ec /usr/local/bin/k9s /usr/local/bin/minikube /usr/local/bin/kubectl > /usr/local/share/go-clis/binaries.sha256
