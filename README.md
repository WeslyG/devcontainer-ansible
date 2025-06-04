## Devcontainer Ansible vscode

Контейнер для разработки на ansible

Контейнер с доклада https://rutube.ru/video/4f714749277839fba776b057db4cd791/ 

Поддерживает архитектуры arm64/amd64
Проверен запуск на windows 11 + wsl2 и на маке с m1 + процессорами

#### Важно

- В ветке kubespray версии пакетов для работы с Kubepsray
- Есть ветка для последнего Ansible (11)

- Python 3.13
- Bookworm Debian 12

Поддерживает:
- Разработку модулей python (pylint, isort, black-formatter)
- Разработку на ansible (поддержка файлов yaml = ansible - может вызывать проблемы при работе с k8s/helm) а также плагины для поддержки синтаксиса ansible, linter ansible
- Полный набор утилит для yaml (линтеры, форматтеры, подсветки отступов и конфигурация yamllint для линтера)
- Shellcheck для sh (потому что он все равно будет)
- Editorconfig
- Helm - поддержка синтаксиса, а также лайв рендеринг шаблонов
- Все версии всех пакетов фиксированы (кроме apt)
- hashicorp устанавливается из РФ

Ну и мелочи:
- base64 экстеншен
- проверка очепяток (ru/en языки),
- проверка странных русских букв С там где их быть не должно
- openssl экстеншен (просмотр сертификатов)
- haproxy/nginx conf + formatter расширения
- kubernetes extension
- git + todo tree

Утилиты:
- hashicorp vault
- hashicorp terraform
- helm
- kubectl
- kubens/kubectx
- minkube (ну на всякий случай)
- k9s
- apt пакеты для всего нужного (если что добавляйте)
  - curl,stow,ca-certificates,nano,iputils-ping,nmap,jq,shellcheck,s3cmd,ncdu,sshpass,dnsutils
- docker (для тестов молекулой)

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

Можно примантировать dotfiles вот так

```

 "mounts": [
     "source=${localEnv:HOME}${localEnv:USERPROFILE}/.ssh/,target=/home/vscode/.ssh,readonly,type=bind",
     "source=${localEnv:HOME}${localEnv:USERPROFILE}/.dotfiles,target=/home/vscode/.dotfiles,type=bind",
     "source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind"
   ],
   "initializeCommand": "mkdir -p ~/.dotfiles", // выполнится на вашем компьютере
   "postCreateCommand": "stow --dir=$HOME/.dotfiles --target=$HOME . && sudo chown vscode:docker /var/run/docker.sock", // выполнится в devcontainer
```

И запуститесь в vscode

### Почему нет latest тега?

Тогда vscode никогда не поймет, когда ребилдится, поэтому лучше, чтобы тег всегда был фисирован!