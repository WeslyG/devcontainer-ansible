## Devcontainer Ansible vscode

Контейнер для разработки на ansible

Поддерживает архитектуры arm64/amd64 
Проверенн запуск на windows 11 + wsl2 и на маке с m1 + процессорами

#### Важно

- В ветке kubespray версии пакетов для работы с Kubepsray
- утилиты hashicorp ставятся с зеркала доступного в рф

Включает в себя:
- python 3.12
- debian bookworm
- ansible (netaddr/dnspython)
- molecule with docker (+ testinfra)
- ansible-lint/yamllint/flake8
- ready for work with Hashicorp vault (hvac + vault cli)
- ready for work with kubepsray
- ready for work with kubernetes (kubectl kubectx kubens helm minikube)
- docker
- apt packages (curl,stow,ca-certificates,nano,iputils-ping,nmap,jq,shellcheck,s3cmd)

Дополнительно:
- Расширения для работы с terraform/haproxy/nginx
- Настройка парсинга ansible + линтеры
- Настройка линтеров для питона
- shellcheck


Использование:

Создайте в своем репозитории папку `.devcontainer` с файлом `devcontainer.json`

С содержимым (уточнить актуальную версию тега)

```
{
  "name": "my-infra",
  "image": "weslyg/ansible-infra:TAG_VERSION",
  "runArgs": [
    "--cap-add=SYS_ADMIN",  // Optional: Adds capabilities required by some applications
    "--net=host"            // Optional: Удобно, ходить в kubernetes и другие службы на локальном компе
  ],
  "mounts": [
    "source=${localEnv:HOME}${localEnv:USERPROFILE}/.ssh/,target=/home/vscode/.ssh,readonly,type=bind",
    "source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind"
  ],
  "postCreateCommand": "sudo chown vscode:docker /var/run/docker.sock",
  "remoteUser": "vscode"
}
```

И запуститесь в vscode

### Почему нет latest тега?

Тогда vscode никогда не поймет, когда ребилдится, поэтому лучше, чтобы тег всегда был фисирован!