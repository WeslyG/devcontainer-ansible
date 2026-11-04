ARG PYTHON_IMAGE=python:3.14.10-slim-trixie@sha256:930e1abba7c4e8f96ed93e8012c35d174d7732752731bbd5e8e757d7ec6f3966

ARG GIT_BUILDER_IMAGE=debian:trixie-slim@sha256:f6b08b09a05725f9431502d3b5714f5c4576e82c1a84fa1debe0c24a7e0c3ec4
FROM ${GIT_BUILDER_IMAGE} AS git-builder
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
COPY --chmod=0755 .devcontainer/cache-cleanup.sh /usr/local/share/cache-cleanup.sh
# Each feature's RUN is cleaned before Docker commits its layer.
SHELL ["/usr/local/share/cache-cleanup.sh", "-c"]
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates curl libexpat1 libpcre2-8-0 libmagic1t64 make perl \
    && rm -rf /var/lib/apt/lists/*

ARG REQUIREMENTS_FILE=requirements/ansible14.txt
ARG ANSIBLE_MAJOR=14
ENV ANSIBLE_MAJOR=${ANSIBLE_MAJOR}
COPY ${REQUIREMENTS_FILE} /tmp/requirements.txt
RUN python -m pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && python -m pip check \
    && rm /tmp/requirements.txt \
    && printf "ansible%s-python%s\n" "$ANSIBLE_MAJOR" "$PYTHON_VERSION" > /etc/platform_version

COPY --from=git-builder /git-runtime/usr/local/ /usr/local/
