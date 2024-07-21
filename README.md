## Devcontainer Ansible vscode

Контейнер для разработки на ansible

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

С содержимым

```
{
  "name": "my-infra",
  "image": "weslyg/ansible-infra:1.0.8",
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