#!/usr/bin/env bash
set -euo pipefail
version="${BIND_VERSION:?}"
digest="${BIND_SHA256:?}"
apt-get update
apt-get install -y --no-install-recommends libuv1-dev liburcu-dev libnghttp2-dev libcap-dev libidn2-dev libkrb5-dev libedit-dev pkg-config
curl -fsSL --retry 3 "https://downloads.isc.org/isc/bind9/${version}/bind-${version}.tar.xz" -o /tmp/bind.tar.xz
echo "$digest  /tmp/bind.tar.xz" | sha256sum --check
mkdir /tmp/bind
tar -xJf /tmp/bind.tar.xz -C /tmp/bind --strip-components=1
cd /tmp/bind
LDFLAGS="-Wl,-rpath,/usr/local/lib/ansible-dns" ./configure --prefix=/usr/local --libdir=/usr/local/lib/ansible-dns --without-lmdb \
    --without-libxml2 --without-json-c --without-jemalloc --disable-geoip \
    --disable-dnstap --with-readline=libedit
make -j"$(nproc)" -C lib
make -j"$(nproc)" -C bin/dig
mkdir -p /dns-runtime/usr/local/lib/ansible-dns
shopt -s nullglob
libraries=(lib/*/.libs/lib*.so*)
test "${#libraries[@]}" -gt 0
cp -a "${libraries[@]}" /dns-runtime/usr/local/lib/ansible-dns/
find /dns-runtime/usr/local/lib/ansible-dns -type f -exec strip {} +
mkdir -p /dns-runtime/usr/local/bin /dns-runtime/usr/local/share/licenses/bind
for command in dig nslookup host; do
    install -m 0755 "bin/dig/.libs/$command" "/dns-runtime/usr/local/bin/$command"
    strip "/dns-runtime/usr/local/bin/$command"
    LD_LIBRARY_PATH=/dns-runtime/usr/local/lib/ansible-dns ldd "/dns-runtime/usr/local/bin/$command" | tee "/tmp/$command.ldd"
    if grep -E 'lmdb|not found' "/tmp/$command.ldd"; then exit 1; fi
done
cp COPYRIGHT LICENSE /dns-runtime/usr/local/share/licenses/bind/
