ARG PYTHON_IMAGE=python:3.12.16-slim-trixie

FROM ${PYTHON_IMAGE} AS git-builder
ARG GIT_VERSION=2.56.0
ARG GIT_SHA256=26c56c296b38c0695b26fa95f475f1d01704d2d38e73465ca30b0b2f5dc789d3
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential ca-certificates curl gettext libcurl4-openssl-dev \
        libexpat1-dev libpcre2-dev libssl-dev xz-utils zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL --retry 3 "https://www.kernel.org/pub/software/scm/git/git-${GIT_VERSION}.tar.xz" -o /tmp/git.tar.xz \
    && echo "${GIT_SHA256}  /tmp/git.tar.xz" | sha256sum --check \
    && mkdir /tmp/git \
    && tar -xJf /tmp/git.tar.xz -C /tmp/git --strip-components=1 \
    && make -s -C /tmp/git -j"$(nproc)" prefix=/usr/local sysconfdir=/etc \
        USE_LIBPCRE=YesPlease NO_RUST=YesPlease NO_TCLTK=YesPlease PYTHON_PATH=/usr/local/bin/python3 all \
    && make -s -C /tmp/git prefix=/usr/local sysconfdir=/etc \
        USE_LIBPCRE=YesPlease NO_RUST=YesPlease NO_TCLTK=YesPlease PYTHON_PATH=/usr/local/bin/python3 DESTDIR=/git-runtime install

FROM ${PYTHON_IMAGE}
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
COPY --chmod=0755 cache-cleanup.sh /usr/local/share/cache-cleanup.sh
# Each feature's RUN is cleaned before Docker commits its layer.
SHELL ["/usr/local/share/cache-cleanup.sh", "-c"]
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates curl libexpat1 libpcre2-8-0 libmagic1t64 make perl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
COPY platform_version.txt /etc/platform_version
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt \
    && python -m pip check \
    && rm /tmp/requirements.txt

COPY --from=git-builder /git-runtime/usr/local/ /usr/local/


# One fixed Node.js runtime; no language-version manager is installed.
ARG NODE_VERSION=24.22.2
ARG NODE_SHA256_AMD64=48cc0e21e048790e54c0cf5749c2725005313d652651c40b7a21feb9697aaf75
ARG NODE_SHA256_ARM64=eb187837a2230d4047161ac0be008584e16b46f726e9c9490ee35dc6b17d9ba8
RUN --mount=type=bind,source=install-node.sh,target=/tmp/install-node.sh \
    apt-get update \
    && apt-get install -y --no-install-recommends libatomic1 libstdc++6 xz-utils \
    && /bin/bash /tmp/install-node.sh
