ARG PYTHON_IMAGE=python:3.14.10-slim-trixie@sha256:22eafb370920ad8b429e0aec3fff433e0669968519f5d60469d83729c138b28b

ARG GIT_BUILDER_IMAGE=debian:trixie-slim@sha256:8aa5a7bf5a1955bddbe7d74fcdd0b91ab30e74362a8b73af672b0481b35b44a0
FROM ${GIT_BUILDER_IMAGE} AS git-builder
ARG GIT_VERSION=2.56.1
ARG GIT_SHA256=f0b0bf89264b9bd2e1c640363e7529643989da76281600473c50745cd34a607f
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential ca-certificates curl gettext libcurl4-openssl-dev \
        libexpat1-dev libpcre2-dev libssl-dev xz-utils zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL --retry 3 "https://www.kernel.org/pub/software/scm/git/git-${GIT_VERSION}.tar.xz" -o /tmp/git.tar.xz \
    && echo "${GIT_SHA256}  /tmp/git.tar.xz" | sha256sum --check \
    && mkdir /tmp/git \
    && tar -xJf /tmp/git.tar.xz -C /tmp/git --strip-components=1 \
    && make -s -C /tmp/git -j"$(nproc)" prefix=/usr/local sysconfdir=/etc CFLAGS="-O2" LDFLAGS="-Wl,-s" \
        USE_LIBPCRE=YesPlease NO_RUST=YesPlease NO_TCLTK=YesPlease PYTHON_PATH=/usr/local/bin/python3 all \
    && make -s -C /tmp/git prefix=/usr/local sysconfdir=/etc CFLAGS="-O2" LDFLAGS="-Wl,-s" \
        USE_LIBPCRE=YesPlease NO_RUST=YesPlease NO_TCLTK=YesPlease PYTHON_PATH=/usr/local/bin/python3 DESTDIR=/git-runtime install

RUN mkdir -p /git-runtime/DEBIAN \
    && printf 'Package: git\nVersion: 1:%s\nArchitecture: %s\nMaintainer: Ansible infra maintainers\nDepends: libcurl4t64, libexpat1, libpcre2-8-0, zlib1g, perl\nDescription: Git built from checksum-pinned upstream source\n' "$GIT_VERSION" "$(dpkg --print-architecture)" > /git-runtime/DEBIAN/control \
    && dpkg-deb --build --root-owner-group /git-runtime /git.deb

FROM git-builder AS dns-builder
ARG BIND_VERSION=9.20.31
ARG BIND_SHA256=9bfecd503ec79209d321053689c794da9f8dba993a24e9cd6bd7aa87cdf4122f
COPY .devcontainer/build/dns-tools.sh /tmp/build-dns.sh
RUN bash /tmp/build-dns.sh

FROM dns-builder AS ssh-builder
ARG OPENSSH_VERSION=10.6p2
ARG OPENSSH_SHA256=9ae44872090cf2f06b3cf9ff147e7f16f309671340763ed2f99248398ae29d5b
COPY .devcontainer/build/ssh-client.sh /tmp/build-ssh.sh
RUN bash /tmp/build-ssh.sh

FROM git-builder AS go-cli-builder
ARG GILT_VERSION=2.2.5
ARG GO_VERSION=1.27.4
ARG GO_SHA256_AMD64=7226736c2339719cda28fbf3a54d71aa63bcefe376e98cef00034268dab24840
ARG GO_SHA256_ARM64=3392582988a273a87ab5043ee1b2c9c17a2c3c00580bf9326c47a2e0aaaeac92
ARG GILT_SOURCE_SHA256=c495dcd9135935f28bdd4acadf2198e3fec6d75912dd33dafc9cb26f08f18ac2
ARG GILT_CRYPTO_VERSION=v0.59.0
ARG GILT_TEXT_VERSION=v0.44.0
ARG EDITORCONFIG_VERSION=4.0.2
ARG EDITORCONFIG_SOURCE_SHA256=0b84c5090d3f48db1bdfab454b7cde79adb26015d1a2731bba59bc1a636276bb
COPY .devcontainer/features/gilt /tmp/go-cli-feature
RUN --mount=type=cache,id=ansible-go-modules,target=/go-module-cache \
    --mount=type=cache,id=ansible-go-build,target=/go-build-cache \
    apt-get update && apt-get install -y --no-install-recommends jq && dpkg -i /git.deb \
    && GOMODCACHE=/go-module-cache GO_BUILD_CACHE=/go-build-cache VERSION="$GILT_VERSION" GOVERSION="$GO_VERSION" \
       GOSHA256AMD64="$GO_SHA256_AMD64" GOSHA256ARM64="$GO_SHA256_ARM64" \
       SOURCESHA256="$GILT_SOURCE_SHA256" CRYPTOVERSION="$GILT_CRYPTO_VERSION" \
       TEXTVERSION="$GILT_TEXT_VERSION" EDITORCONFIGVERSION="$EDITORCONFIG_VERSION" \
       EDITORCONFIGSOURCESHA256="$EDITORCONFIG_SOURCE_SHA256" bash /tmp/go-cli-feature/install.sh \
    && mkdir -p /go-runtime/usr/local/bin /go-runtime/usr/local/share \
    && cp -a /usr/local/bin/gilt /usr/local/bin/ec /usr/local/bin/editorconfig-checker /usr/local/bin/k9s /usr/local/bin/minikube /usr/local/bin/kubectl /go-runtime/usr/local/bin/ \
    && cp -a /usr/local/share/gilt /usr/local/share/editorconfig-checker /usr/local/share/go-clis /go-runtime/usr/local/share/ \
    && find /go-runtime -exec touch -h -d @0 {} +

FROM ${PYTHON_IMAGE}
ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_COMPILE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
COPY --chmod=0755 .devcontainer/cache-cleanup.sh /usr/local/share/cache-cleanup.sh
# Each feature's RUN is cleaned before Docker commits its layer.
SHELL ["/usr/local/share/cache-cleanup.sh", "-c"]
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates curl libexpat1 libpcre2-8-0 libmagic1t64 make perl \
        libuv1t64 liburcu8t64 libnghttp2-14 libcap2 libidn2-0 libkrb5-3 libgssapi-krb5-2 libedit2 libfido2-1 libcbor0.10 \
    && rm -rf /var/lib/apt/lists/*

ARG REQUIREMENTS_FILE=requirements/ansible14.txt
ARG ANSIBLE_MAJOR=14
ENV ANSIBLE_MAJOR=${ANSIBLE_MAJOR}
RUN --mount=type=bind,source=${REQUIREMENTS_FILE},target=/tmp/requirements.txt \
    --mount=type=bind,source=.devcontainer/build/install-python.py,target=/tmp/install-python.py \
    python /tmp/install-python.py \
    && find /usr/local/lib -type d -name __pycache__ -prune -exec rm -rf {} +

RUN --mount=type=bind,from=git-builder,source=/git.deb,target=/tmp/git.deb dpkg -i /tmp/git.deb
RUN --mount=type=bind,from=ssh-builder,source=/openssh-client.deb,target=/tmp/openssh-client.deb dpkg -i /tmp/openssh-client.deb
COPY --from=dns-builder /dns-runtime/usr/local/ /usr/local/
COPY --from=go-cli-builder /go-runtime/usr/local/bin/ /usr/local/bin/
COPY --from=go-cli-builder /go-runtime/usr/local/share/ /usr/local/share/

# The build runner/CI chooses one dated release identity for the whole matrix.
ARG PLATFORM_VERSION
ENV PLATFORM_VERSION=${PLATFORM_VERSION}
LABEL org.opencontainers.image.version=${PLATFORM_VERSION}
RUN test -n "$PLATFORM_VERSION" && printf '%s\n' "$PLATFORM_VERSION" > /etc/platform_version
