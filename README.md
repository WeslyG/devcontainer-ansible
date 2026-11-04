## Devcontainer Ansible vscode

Контейнер для разработки на ansible

Контейнер с доклада https://rutube.ru/video/4f714749277839fba776b057db4cd791/ 

Поддерживает архитектуры arm64/amd64
Проверен запуск на windows 11 + wsl2 и на маке с m1 + процессорами

#### Важно

- В ветке kubespray версии пакетов для работы с Kubepsray
- Ветка `ansible10`: Ansible 10.7.0, ansible-core 2.17.14

- Python 3.12
- slim-trixie Debian 13, один Python 3.12

Зависимости: `bcrypt==4.3.0` оставлен для совместимости с `passlib==1.7.4`; bcrypt 5 ломает инициализацию backend. Ansible 10 использует Python 3.10–3.12 в контейнере и Python 3.7–3.12 на целевых узлах. Molecule, ansible-lint и ansible-compat зафиксированы на последних совместимых версиях 26.6.0: новые версии исключают ansible-core 2.17.

Поддерживает:
- Разработку модулей python (pylint, isort, black-formatter)
- Разработку на ansible (поддержка файлов yaml = ansible - может вызывать проблемы при работе с k8s/helm) а также плагины для поддержки синтаксиса ansible, linter ansible
- Полный набор утилит для yaml (линтеры, форматтеры, подсветки отступов и конфигурация yamllint для линтера)
- Shellcheck для sh (потому что он все равно будет)
- Editorconfig
- Helm - поддержка синтаксиса, а также лайв рендеринг шаблонов
- Python-зависимости фиксированы в requirements.txt, внешние devcontainer features — в lockfile; apt-пакеты обновляются при сборке; Node.js, Git и Claude Code фиксированы
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
- Node.js 24.22.2, npm и npx — напрямую из официального архива
- s3cmd и Python yq на том же Python 3.12
- apt пакеты для всего нужного (если что добавляйте)
  - curl,stow,ca-certificates,nano,iputils-ping,nmap,jq,shellcheck,ncdu,sshpass,dnsutils,ldap-utils
- Docker CLI, Buildx и Compose используют Docker хоста (для тестов Molecule); daemon внутри образа отсутствует

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
    "source=${localEnv:HOME}${localEnv:USERPROFILE}/.ssh/,target=/home/vscode/.ssh,readonly,type=bind"
  ],
  "remoteUser": "vscode"
}
```

Можно примантировать dotfiles вот так

```

 "mounts": [
     "source=${localEnv:HOME}${localEnv:USERPROFILE}/.ssh/,target=/home/vscode/.ssh,readonly,type=bind",
     "source=${localEnv:HOME}${localEnv:USERPROFILE}/.dotfiles,target=/home/vscode/.dotfiles,type=bind"
   ],
   "initializeCommand": "mkdir -p ~/.dotfiles", // выполнится на вашем компьютере
   "postCreateCommand": "stow --dir=$HOME/.dotfiles --target=$HOME .", // выполнится в devcontainer
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
  -v /var/run/docker.sock:/var/run/docker-host.sock \
  -v "$PWD/.devcontainer/tests:/tests:ro" \
  ansible10-local:verify sh /tests/molecule.sh
```

Smoke-тест проверяет Python 3.12, Ansible 10 / ansible-core 2.17,
`pip check`, CLI-утилиты, импорты, Ansible Vault, ansible-lint и выполнение playbook.
Обычный тест Molecule создаёт один внешний целевой контейнер с Python 3.12,
выполняет converge, idempotence и verify, затем удаляет его.
Проверка старого целевого узла Python 3.7 включается только явно: передайте
`-e TEST_LEGACY_PYTHON=1` контейнеру с тестами. Python 3.7 не устанавливается
в рабочий devcontainer. Требуется доступ к Docker socket.


### Размер и один Python

База `python:3.12.16-slim-trixie` сохраняет Debian 13 и Python 3.12.
Python-утилиты s3cmd/yq устанавливаются через pip на этот же интерпретатор;
Node.js устанавливается непосредственно в `/usr/local` из официального архива
с проверкой SHA256 для amd64/arm64. NVM и другие менеджеры версий языков,
Corepack и шими Yarn/pnpm отсутствуют. Доступны Node.js, npm и npx.
Системный Python Debian и дополнительные Python-окружения не требуются.

Git 2.56.0 собирается в отдельной стадии с проверкой SHA256 исходного архива.
В конечный образ копируется готовый Git CLI, без компиляторов и заголовков.
Для сборки собственных нативных расширений компиляторы потребуется установить отдельно.

Claude Code и minikube сохранены. Claude хранит один native бинарник;
глобальная команда использует ссылку на пользовательский launcher.
Docker-outside-of-Docker автоматически подключает сокет Docker хоста и
настраивает доступ для `vscode`. Compose доступен как `docker compose`.
Пакетные кеши pip/npm исключаются в момент установки, а не удаляются поздним слоем.


Измерено для linux/amd64 через `docker image inspect`: **6,26 → 3,46 ГБ**
без сжатия, сокращение **44,8%**. Размер кеша сборки и старых образов считается
отдельно. Smoke-тесты и Molecule на Python 3.7/3.12 прошли от `vscode`
через Docker хоста.

При обновлении Git меняйте `GIT_VERSION` и `GIT_SHA256` в Dockerfile;
контрольная сумма публикуется в `sha256sums.asc` на kernel.org.
Версия базового Python задаётся через `PYTHON_IMAGE`.


### Кеши сборки

Dockerfile использует shell-обёртку для `RUN`: после успешной команды она
очищает apt archives/lists, pip/npm-кеши root и пользователей, временные архивы
и временную загрузку k9s. Очистка происходит до сохранения слоя, включая
слои devcontainer features. Интерактивный shell и entrypoint контейнера не меняются.

`apt-get update` и `apt-get install` следует выполнять в одном `RUN`.
Кеш pip и проверка его обновлений отключены через переменные окружения.
Проверка чистого образа: `python .devcontainer/tests/caches.py` от root
в одноразовом контейнере до запуска инструментов, которые могут создать новый кеш.


Версия Node.js и SHA256 архивов для amd64/arm64 задаются через `NODE_VERSION`,
`NODE_SHA256_AMD64`, `NODE_SHA256_ARM64` в Dockerfile. Для обновления Node.js
пересоберите образ с новой зафиксированной версией и контрольными суммами;
менеджер переключения версий для этого не используется.
