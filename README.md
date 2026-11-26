# Ansible devcontainers: 10, 12 и 14

Ветка `main` содержит три образа из общего Dockerfile, локальных features и
тестов. Конфигурация по умолчанию — Ansible 14. GitHub Actions собирает и
проверяет каждый вариант на native amd64/arm64 и публикует образы в
[`weslyg/ansible-infra`](https://hub.docker.com/r/weslyg/ansible-infra).

<!-- security-badges:start -->
[![Trivy: 2026.11.27](https://img.shields.io/badge/Trivy-2026.11.27-blue?style=flat-square)](https://github.com/WeslyG/devcontainer-ansible/actions/runs/45889510824)

| Ansible | amd64 | arm64 |
| --- | --- | --- |
| 10 | [![Ansible 10 amd64: 96 High/Critical](https://img.shields.io/badge/amd64-96%20High%2FCritical-red?style=flat-square)](https://github.com/WeslyG/devcontainer-ansible/actions/runs/45889510824) | [![Ansible 10 arm64: 96 High/Critical](https://img.shields.io/badge/arm64-96%20High%2FCritical-red?style=flat-square)](https://github.com/WeslyG/devcontainer-ansible/actions/runs/45889510824) |
| 12 | [![Ansible 12 amd64: 96 High/Critical](https://img.shields.io/badge/amd64-96%20High%2FCritical-red?style=flat-square)](https://github.com/WeslyG/devcontainer-ansible/actions/runs/45889510824) | [![Ansible 12 arm64: 96 High/Critical](https://img.shields.io/badge/arm64-96%20High%2FCritical-red?style=flat-square)](https://github.com/WeslyG/devcontainer-ansible/actions/runs/45889510824) |
| 14 | [![Ansible 14 amd64: 96 High/Critical](https://img.shields.io/badge/amd64-96%20High%2FCritical-red?style=flat-square)](https://github.com/WeslyG/devcontainer-ansible/actions/runs/45889510824) | [![Ansible 14 arm64: 96 High/Critical](https://img.shields.io/badge/arm64-96%20High%2FCritical-red?style=flat-square)](https://github.com/WeslyG/devcontainer-ansible/actions/runs/45889510824) |

Счётчики находок High/Critical учитывают согласованные исключения Ansible 10.
Полные JSON/SBOM — в [Artifacts этого скана](https://github.com/WeslyG/devcontainer-ansible/actions/runs/45889510824#artifacts).
<!-- security-badges:end -->

## Матрица совместимости

<!-- compatibility:start -->
| Образ | Ansible | ansible-core | Python контроллера | Поддерживаемый Python на удалённых хостах | Molecule | ansible-lint / ansible-compat |
|---|---|---|---|---|---|---|
| 10 | 10.7.0 | 2.17.14 | 3.12.16 | 3.7–3.12 | 26.6.0 | 26.6.0 / 26.6.0 |
| 12 | 12.3.0 | 2.19.15 | 3.13.18 | 3.8–3.13 | 26.11.1 | 26.11.1 / 26.11.1 |
| 14 | 14.6.0 | 2.21.6 | 3.14.10 | 3.9–3.14 | 26.11.1 | 26.11.1 / 26.11.1 |
<!-- compatibility:end -->

Версии соответствуют дате `updatedAt` в `images.json`. Python контроллера
выбирается в пределах поддержки ansible-core по
[официальной матрице Ansible](https://docs.ansible.com/projects/ansible-core/2.21/reference_appendices/release_and_maintenance.html).
Диапазоны Python на удалённых хостах включают обе границы. Коллекции и модули
могут предъявлять дополнительные требования к Python и установленным библиотекам.
Molecule проверяет внешний узел на версии Python соответствующего контроллера;
полный диапазон удалённых Python указан как upstream-совместимость.

Ограничения разрешения зависимостей:

- Ansible 10 использует core 2.17 и совместимые Molecule, ansible-lint и ansible-compat.
- Ansible 12 использует core 2.19, Ansible 14 — core 2.21.
- `bcrypt<5` закрепляет совместимость backend passlib. Smoke-тесты проверяют
  bcrypt roundtrip и Ansible `password_hash`.
- Общие Python-зависимости разрешаются до последних стабильных совместимых
  версий. yq предоставляет jq-совместимый интерфейс, проверяемый smoke-тестом.

Полные выбранные версии находятся в `compatibility/resolved.json`, сравнение
selected/latest с причинами ограничений — в `compatibility/packages.json`.
Зафиксированные native-прогоны и размеры — в `compatibility/validation.json`.

## Состав образов

<!-- tools:start -->
| Инструмент | Версия |
|---|---|
| Node.js | 26.13.1 |
| npm | 12.2.3 |
| Git | 2.56.1 |
| Claude Code | 2.1.332 |
| elasticdump | 6.125.1 |
| kubectl | 1.37.3 |
| Helm | 4.3.2 |
| minikube | 1.39.0 |
| k9s | 0.51.0 |
| Gilt | 2.2.5 |
| OpenSSH client | 10.6p2 |
| BIND DNS clients | 9.20.31 |
| EditorConfig checker | 4.0.2 |
| devcontainer CLI (host/CI) | 0.91.0 |
<!-- tools:end -->

Каждый образ содержит один Python из официального `python:*-slim-trixie`,
Ansible и вспомогательные Python-пакеты. Полные транзитивные версии и SHA256
зафиксированы в `requirements/ansible{10,12,14}.txt`; установка использует
`--require-hashes` и проверку `pip check`.

Node устанавливается локальной feature из официального архива с SHA256 для
amd64/arm64. npm и npx входят в инструментальную среду. NVM, fnm, asdf, mise,
pyenv, uv, pipx, conda, Corepack, Yarn и pnpm отсутствуют.
Gilt и EditorConfig checker собираются из официальных source releases с проверкой
SHA256 и upstream-тестами. Общий Go toolchain и его caches удаляются в том же RUN.
Git, OpenSSH client и DNS-клиенты BIND собираются в отдельных стадиях. Git и
OpenSSH зарегистрированы как deb-пакеты с Debian epoch; apt использует эти
версии. Runtime содержит один набор исполняемых файлов без компиляторов.
BIND собирается без LMDB; dig, nslookup и host доступны.

Claude Code представлен одним native-бинарником из официального платформенного
npm-архива Anthropic с SHA512 integrity. Команда доступна через symlink;
пользовательская установка принадлежит `vscode`. Образы также содержат
minikube, kubectl, Helm, k9s и elasticdump.

Docker используется как CLI с Compose/Buildx. Daemon работает на хосте,
сокет подключает feature docker-outside-of-docker. Docker Desktop должен
предоставлять доступ к daemon из WSL/devcontainer.

## Структура репозитория

```text
images.json                         # версии CLI/actions, Python digests, семейства и бюджеты
requirements/common.in              # общие прямые Python-зависимости
requirements/ansible{10,12,14}.in    # разрешённые семейства Ansible/core
requirements/ansible{10,12,14}.txt   # полные точные locks с SHA256
.devcontainer/Dockerfile            # общий runtime и стадии Git/OpenSSH/BIND
.devcontainer/template.json         # настройки редактора и features
.devcontainer/ansible{10,12,14}/     # конфигурации вариантов и feature locks
.devcontainer/devcontainer.json     # конфигурация по умолчанию
.devcontainer/features/             # Node, Go CLI, Kubernetes, Claude Code/elasticdump
.devcontainer/tests/                # runtime, locks, кеши, Gilt и Molecule
scripts/                            # обновление, генерация, build/test и публикация
compatibility/                      # отчёты зависимостей и измерений
.github/workflow-templates/          # исходники workflows
.github/workflows/                   # сгенерированные workflows
```

`python3 scripts/render.py` генерирует configs, workflows и таблицы README.
`python3 scripts/render.py --check` проверяет соответствие исходникам.
Внешние features закреплены отдельными `devcontainer-lock.json`; локальные
features фиксируются git-коммитом. Сборка использует `--frozen-lockfile`.

## Локальная сборка и тесты

Нужны Docker с Buildx, Python 3.10+, curl, Node/npm и devcontainer CLI версии из
`images.json`. Скрипты на хосте используют стандартную библиотеку Python.
GNU Make предоставляет короткие команды; соответствующие вызовы Python
перечислены в Makefile.

```bash
npm install --global @devcontainers/cli@0.91.0
make check
make test                          # все три образа, сборка и проверки
make test VARIANTS=14              # один вариант
make build VARIANTS='10 12 14'      # сборка без runtime-тестов
make record                        # записать полный успешный native-прогон
```

Путь к CLI можно задать через `DEVCONTAINER_CLI`.
Локальные теги имеют вид `ansible-infra:ansible10-YYYY.MM.DD`.
Для VS Code или прямого вызова devcontainer CLI выберите общую версию выпуска
в окружении, из которого запускается редактор/CLI:

```bash
export PLATFORM_VERSION=$(python3 scripts/version.py)
devcontainer up --workspace-folder . --config .devcontainer/ansible12/devcontainer.json
```

`make build` и `make test` выбирают версию автоматически, если переменная
не задана. Повторная проверка конкретного образа требует его версии:

```bash
PLATFORM_VERSION=2026.11.04 python3 scripts/build.py --variants 12 --test-only
```

Тесты проверяют отсутствие дублирующих исполняемых файлов и Python distributions,
локальные DNS-запросы, OpenSSH keygen/config, Python hash-lock, `pip check`, один Python, отсутствие менеджеров
версий, компилятора и Docker daemon, пустоту кешей, версии CLI, импорты,
yq, bcrypt/Vault, ansible-lint/playbook и Gilt overlay. Версия в ENV,
`/etc/platform_version` и OCI label сверяется с выпуском.
Molecule выполняет create → converge → idempotence → verify → destroy от `vscode`
через daemon хоста. Временные контейнеры имеют уникальные имена и метки;
runner удаляет только ресурсы собственного прогона.

Полные runtime-тесты выполняются на native-архитектуре. Логи, размеры и
идентификаторы проверенных образов находятся в `.build/<arch>/`.

## Размер и кеши

apt lists/archives, pip/npm caches и временные загрузки очищаются в создающем
их слое `RUN`. Общая shell-обёртка применяется и к сторонним features.
Аудит кешей выполняется на чистом образе до запуска пользовательских инструментов.

Размер измеряется в несжатых байтах через `docker image inspect` отдельно для
каждой архитектуры. Runner проверяет `maxImageBytes` из `images.json`.
Повышение бюджета требует анализа роста. Общие слои разных образов учитываются
Docker отдельно от суммы их индивидуальных размеров. Пользовательские образы,
контейнеры, volumes и общий build cache сохраняются.

<!-- sizes:start -->
| Платформа | Тег образа | Несжатый размер | Проверено | Состояние lock |
|---|---|---|---|---|
| amd64 | ansible-infra:ansible10-2026.11.26 | 2,839,099,956 байт | 2026-11-26 | текущий |
| amd64 | ansible-infra:ansible12-2026.11.26 | 2,857,919,627 байт | 2026-11-26 | текущий |
| amd64 | ansible-infra:ansible14-2026.11.26 | 2,865,606,541 байт | 2026-11-26 | текущий |
<!-- sizes:end -->

Таблица строится из зафиксированных измерений. Состояние «требует проверки»
означает несовпадение проверенных входных данных с текущими manifest/locks.
Результаты CI доступны в артефактах соответствующего запуска.

## Дата выпуска и теги Docker Hub

В начале сборки выбирается дата в часовом поясе `Asia/Yekaterinburg`, строго
`YYYY.MM.DD` с ведущими нулями. Повторные выпуски за день получают `-1`, `-2`
и следующие номера. Одна версия применяется ко всей матрице.

Multiarch-теги:

```text
weslyg/ansible-infra:ansible10-2026.11.04
weslyg/ansible-infra:ansible12-2026.11.04
weslyg/ansible-infra:ansible14-2026.11.04
weslyg/ansible-infra:ansible14-2026.11.04-1
```

Каждый такой тег содержит `linux/amd64` и `linux/arm64`. Регулярное выражение:
`^ansible(10|12|14)-(\d{4}\.\d{2}\.\d{2})(?:-([1-9]\d*))?$`.
Native-теги имеют префикс архитектуры, например
`amd64-ansible14-2026.11.04` и `arm64-ansible14-2026.11.04`.
Слои native-образов и multiarch-манифеста совместно используются registry.

Локальный выбор учитывает локальные теги. CI читает все страницы опубликованных
native- и multiarch-тегов Docker Hub и выбирает свободный номер. Native-теги
учитываются и при неполном выпуске. Ошибка registry останавливает выбор версии.
Запуски workflow для `main` выполняются последовательно от выбора версии до
публикации, без отмены выполняющегося выпуска.

`PLATFORM_VERSION` и CI-переменная `TAG_VERSION` содержат дату с необязательным номером. То же значение
записано в `/etc/platform_version`, ENV образа, OCI label
`org.opencontainers.image.version` и отчёты сборки.

```bash
RELEASE='YYYY.MM.DD' # подставить версию успешной job publish
docker pull "weslyg/ansible-infra:ansible14-${RELEASE}"
```

## GitHub Actions

`build.yml` запускается при push в `main`, в PR и вручную:

1. На `main` проверяет авторизацию Docker Hub и выбирает общую версию выпуска.
2. Собирает и полностью тестирует матрицу Ansible 10/12/14 × amd64/arm64.
   В каждом native-задании сначала проверяет общий Go builder, затем освобождает
   его compiler/module cache mounts на одноразовом runner. Готовый слой CLI
   переиспользуется при сборке runtime-образа.
3. На `main` каждое успешное native-задание отправляет проверенный образ в
   Docker Hub под native-тегом и сохраняет digest/идентичность образа в артефакт.
4. После успеха всех шести заданий job `publish` проверяет шесть отчётов,
   создаёт три multiarch-тега по точным digest и проверяет состав манифестов.
5. Опциональная job `scan-published` после публикации запускает Trivy для всех
   трёх вариантов на каждой архитектуре по точным опубликованным native digest.
   Её статус отображается отдельно. High/Critical вне согласованных исключений
   дают ошибку сканирования; опубликованные образы остаются доступны.

При ручном запуске скан управляется флагом `scan_published` (включён по умолчанию).
Для push в `main` он включён, если repository variable `SCAN_PUBLISHED_IMAGES`
не равна строке `false`. В Artifacts запуска находятся
`security-<release>-<arch>-attempt<N>`: полный JSON Trivy, CycloneDX SBOM,
политика находок, digest образа, Git revision, версия сканера и SHA256 базы CVE.
Сводка доступна в job summary. Каждый повтор job сохраняет отдельный снимок;
срок хранения соответствует настройке GitHub Actions retention репозитория.
Правила разбора находок: [политика безопасности](docs/security.md).

PR и ручные запуски других веток выполняют сборку и тесты. Авторизация Docker Hub
и публикация доступны push/ручному запуску `main`. GitHub token имеет
`contents: read`. Публикация использует repository secrets:

- `DOCKERHUB_USERNAME` — пользователь с правами записи в `weslyg/ansible-infra`;
- `DOCKERHUB_TOKEN` или `DOCKERHUB_PASSWORD` — Docker Hub access token/пароль.

Публикация использует Docker Engine API 1.46+ (Docker 27+) и сверяет ID
локального образа после тестов, затем сравнивает контрольные суммы слоёв
и настройки запуска с опубликованным образом.
Занятый тег с другим содержимым вызывает ошибку; повтор того же job может
использовать идентичный опубликованный образ. Сборка пакетов при push не выполняется.
Native-теги доступны независимо; наличие multiarch-тега означает успех всей
native-матрицы и проверку итогового манифеста.

CI экспортирует только явно перечисленные публичные отчёты из `scripts/artifacts.py`.
Скрытые файлы, credentials и весь каталог `.build` в артефакты не включаются.
При ошибке последние 80 строк build/test-лога выводятся в CI log.

## Обновление зависимостей

```bash
make audit
make update
make check
make test BUILD_FLAGS=--no-cache
make record
make security VARIANT=10 ARCH=amd64
git diff --check
git diff
```

`make audit` записывает сведения о выпусках в `.build`. `make update` обновляет
metadata, configs/workflows, Python locks и feature locks. Updater использует
официальные Python/Node/PyPI/npm registries, GitHub Releases, kernel.org и
Kubernetes stable.txt. Выбираются стабильные совместимые выпуски.
Python base фиксируется patch-тегом и multiarch digest. Pip resolver работает
в Python каждого варианта; lock включает SHA256 всех non-yanked артефактов
для установки amd64/arm64 wheels. Финальная сборка проверяет применимость lock.

Для релизного обновления `--no-cache` освежает apt и build dependencies.
Версии GitHub Actions находятся в `images.json` и обновляются общей автоматикой.
При добавлении Ansible major нужно определить controller/target ranges по
официальной матрице, обновить `FAMILIES` в updater и проверить ограничения пакетов.

`update.yml` по понедельникам и при ручном запуске рассчитывает совместимые
зависимости и выдаёт `update.patch`, latest releases и compatibility reports
как review-артефакт. Применённый patch проходит сборку и тесты в `build.yml`.
Renovate имеет `enabled: false`; источником обновлений служит `scripts/update.py`.
Инструкции для сопровождающих находятся в [AGENTS.md](AGENTS.md).

## Диагностика runtime

Passlib может вывести сообщение об отсутствии `bcrypt.__about__` с bcrypt
4.x. Проверки хеширования и Ansible-фильтра должны успешно пройти.
Hashicorp mirror находится вне набора автоматически устанавливаемых инструментов.

Проверки безопасности, SBOM и политика Ansible 10: [docs/security.md](docs/security.md).

Тестовый harness запускает готовый image ID с исходными runtime-настройками devcontainer и UID пользователя образа. Перед smoke/Molecule проверяется совпадение `.Image` контейнера с измеренным image ID. Временная конфигурация запуска находится в `.build/<arch>/runtime-<variant>/devcontainer.json`.

Badges показывают последний проведённый post-publication скан для каждой
версии и архитектуры. `compatibility/security-snapshot.json` сохраняет счётчики,
digest образов, source revision и версию базы CVE. Ошибка или отсутствующий
скан отображаются серым, а не нулём. После сканов job `badges` обновляет только
README и этот снимок коммитом `[skip ci]`. Без нового сканирования бейджи можно
перегенерировать командой `python3 scripts/badges.py`.
