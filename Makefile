# for local usage

install_devcontainer:
	npm i -g @devcontainers/cli

nexus_login:
	echo "$NEXUS_PASSWORD" | docker login --registry-url=https://registry.weslyg.ru --username $NEXUS_USERNAME --password-stdin

dockerhub_login:
	echo "$DOCKERHUB_PASSWORD" | docker login --username $DOCKERHUB_USERNAME --password-stdin

build_and_push_nexus: nexus_login
	devcontainer build --workspace-folder . --platform=linux/amd64,linux/arm64 --image-name registry.weslyg.ru/ansible-infra:$TAG_VERSION --push

build_and_push_dockerhub: dockerhub_login
	devcontainer build --workspace-folder . --platform=linux/amd64,linux/arm64 --image-name weslyg/ansible-infra:$TAG_VERSION --push

run: install_devcontainer build_and_push_dockerhub build_and_push_nexus