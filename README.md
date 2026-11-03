## Devcontainer Ansible vscode

Контейнер для разработки на ansible

Контейнер с доклада https://rutube.ru/video/4f714749277839fba776b057db4cd791/ 

Поддерживает архитектуры arm64/amd64
Проверен запуск на windows 11 + wsl2 и на маке с m1 + процессорами

#### Важно

- В ветке kubespray версии пакетов для работы с Kubepsray
- Ветка `ansible10`: Ansible 10.7.0, ansible-core 2.17.14

- Python 3.12
- trixie Debian 13

Зависимости: `bcrypt==4.3.0` оставлен для совместимости с `passlib==1.7.4`; bcrypt 5 ломает инициализацию backend. Ansible 10 использует Python 3.10–3.12 в контейнере и Python 3.7–3.12 на целевых узлах. Molecule, ansible-lint и ansible-compat зафиксированы на последних совместимых версиях 26.6.0: новые версии исключают ansible-core 2.17.

Поддерживает:
- Разработку модулей python (pylint, isort, black-formatter)
- Разработку на ansible (поддержка файлов yaml = ansible - может вызывать проблемы при работе с k8s/helm) а также плагины для поддержки синтаксиса ansible, linter ansible
- Полный набор утилит для yaml (линтеры, форматтеры, подсветки отступов и конфигурация yamllint для линтера)
- Shellcheck для sh (потому что он все равно будет)
- Editorconfig
- Helm - поддержка синтаксиса, а также лайв рендеринг шаблонов
- Python-зависимости фиксированы в requirements.txt, внешние devcontainer features — в lockfile; apt-пакеты, Git и Claude Code обновляются при сборке
- Gilt устанавливается локальной [feature](.devcontainer/features/gilt/README.md) из GitHub Releases с фиксированной версией и проверкой SHA256
- HashiCorp feature временно отключена: зеркало недоступно

Ну и мелочи:
- base64 экстеншен
- проверка очепяток (ru/en языки),
- проверка странных русских букв С там где их быть не должно
- openssl экстеншен (просмотр сертификатов)
- haproxy/nginx conf + formatter расширения
- kubernetes extension
- git + todo tree (временно пропал из marketplace - https://github.com/FanaticPythoner/better-todo-tree/issues/142)

Утилиты:
- hashicorp vault (временно отключён)
- hashicorp terraform (временно отключён)
- helm
- kubectl
- kubens/kubectx
- minkube (ну на всякий случай)
- k9s
- elasticdump
- apt пакеты для всего нужного (если что добавляйте)
  - curl,stow,ca-certificates,nano,iputils-ping,nmap,jq,yq,shellcheck,s3cmd,ncdu,sshpass,dnsutils,ldap-utils,nodejs,npm
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

### Проверка ветки ansible10

```sh
devcontainer build --workspace-folder . --frozen-lockfile --image-name ansible10-local:verify
docker run --rm --user vscode --workdir /tmp \
  -v "$PWD/.devcontainer/tests:/tests:ro" \
  ansible10-local:verify sh /tests/ansible10.sh
docker run --rm --user vscode --workdir /tmp \
  -v "$PWD/.devcontainer/tests:/tests:ro" \
  ansible10-local:verify bash /tests/gilt-overlay.sh
docker run --rm --workdir /tmp \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$PWD/.devcontainer/tests:/tests:ro" \
  ansible10-local:verify sh /tests/molecule.sh
```

Smoke-тест проверяет Python 3.12, Ansible 10 / ansible-core 2.17,
`pip check`, CLI-утилиты, импорты, Ansible Vault, ansible-lint и выполнение playbook.
Тест Molecule создаёт временные Docker-контейнеры с Python 3.7 и 3.12,
выполняет converge, idempotence и verify, затем удаляет их. Требуется доступ к Docker socket.
