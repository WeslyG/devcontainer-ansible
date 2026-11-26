#!/usr/bin/env bash
set -euo pipefail
test "$(id -u)" -eq 0
for value in "${VERSION:?}" "${HELM:?}" "${MINIKUBE:?}"; do
    [[ "$value" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Specify exact Kubernetes CLI release versions' >&2; exit 1; }
done
case "$(dpkg --print-architecture)" in
    amd64) architecture=amd64; kubectl_sha="${SHA256AMD64:?}"; helm_sha="${HELMSHA256AMD64:?}"; minikube_sha="${MINIKUBESHA256AMD64:?}" ;;
    arm64) architecture=arm64; kubectl_sha="${SHA256ARM64:?}"; helm_sha="${HELMSHA256ARM64:?}"; minikube_sha="${MINIKUBESHA256ARM64:?}" ;;
    *) exit 1 ;;
esac
work_dir="$(mktemp -d)"
trap 'rm -rf -- "$work_dir"' EXIT
fetch() {
    curl --fail --silent --show-error --location --connect-timeout 15 --max-time 240 --retry 2 "$1?ansible-infra=${RANDOM}${RANDOM}" --output "$2"
    printf '%s  %s\n' "$3" "$2" | sha256sum --check
}
if ! [ -f /usr/local/share/go-clis/kubectl/version ] || [ "$(cat /usr/local/share/go-clis/kubectl/version)" != "$VERSION" ]; then
fetch "https://dl.k8s.io/release/v$VERSION/bin/linux/$architecture/kubectl" "$work_dir/kubectl" "$kubectl_sha"
install -m 0755 "$work_dir/kubectl" /usr/local/bin/kubectl
fi
fetch "https://get.helm.sh/helm-v$HELM-linux-$architecture.tar.gz" "$work_dir/helm.tar.gz" "$helm_sha"
if ! [ -f /usr/local/share/go-clis/minikube/version ] || [ "$(cat /usr/local/share/go-clis/minikube/version)" != "$MINIKUBE" ]; then
fetch "https://github.com/kubernetes/minikube/releases/download/v$MINIKUBE/minikube-linux-$architecture" "$work_dir/minikube" "$minikube_sha"
install -m 0755 "$work_dir/minikube" /usr/local/bin/minikube
fi
tar -xzf "$work_dir/helm.tar.gz" -C "$work_dir" --no-same-owner
install -m 0755 "$work_dir/linux-$architecture/helm" /usr/local/bin/helm
kubectl version --client
helm version --short
minikube version --short
