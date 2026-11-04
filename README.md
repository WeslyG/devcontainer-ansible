# Ansible devcontainers: 10, 12 и 14

Одна ветка `main` собирает три независимых образа из общего Dockerfile,
локальных features и тестов. Конфигурация по умолчанию — Ansible 14.
Сборки и workflows ничего не публикуют в реестры и не выполняют git push.

## Матрица совместимости

<!-- compatibility:start -->
| Образ | Ansible | ansible-core | Python контроллера | Python целевых узлов (upstream) | Molecule | ansible-lint / ansible-compat |
|---|---|---|---|---|---|---|
| 10 | 10.7.0 | 2.17.14 | 3.12.16 | 3.7–3.12 | 26.6.0 | 26.6.0 / 26.6.0 |
| 12 | 12.3.0 | 2.19.15 | 3.13.18 | 3.8–3.13 | 26.10.0 | 26.10.1 / 26.10.0 |
| 14 | 14.5.0 | 2.21.6 | 3.14.10 | 3.9–3.14 | 26.10.0 | 26.10.1 / 26.10.0 |
<!-- compatibility:end -->

Это последние стабильные совместимые версии на дату в `images.json`.
Python выбирается по верхней границе поддержки соответствующего ansible-core,
а не только по `Requires-Python` PyPI: эта метаинформация часто задаёт лишь минимум.
Источники: [официальная матрица Ansible](https://docs.ansible.com/projects/ansible-core/2.21/reference_appendices/release_and_maintenance.html),
[PyPI](https://pypi.org/), [официальные Python images](https://hub.docker.com/_/python).
Ansible 10 и 12 — исторические ветки community package; новая major-версия core
в них не подставляется даже тогда, когда pip разрешает более широкий диапазон.

Ограничения совместимости:

- Ansible 10 требует старые совместимые Molecule, ansible-lint и ansible-compat:
  новые версии явно исключают ansible-core 2.17.
- `bcrypt<5`: passlib 1.7.4 проверяет backend длинным паролем, который bcrypt 5
  отклоняет. Smoke-тест выполняет bcrypt roundtrip и Ansible `password_hash`.
- Входные требования остальных Python-пакетов не ограничены старыми версиями:
  resolver каждый раз выбирает свежие совместимые выпуски. В том числе yq
  обновлён до 4.x; его jq-совместимый вызов проверяется тестом.

Все выбранные транзитивные версии: `compatibility/resolved.json`.
Сравнение selected/latest с объяснениями: `compatibility/packages.json`.
Результаты реальных прогонов и размеры: `compatibility/validation.json`;
полная локальная диагностика находится в игнорируемом каталоге `.build/`.
Диапазон поддержки целевых Python в таблице взят из upstream; обычный Molecule
проверяет один внешний узел на версии Python своего контроллера, а не весь диапазон.

## Структура

Общие CLI для всех трёх вариантов:

<!-- tools:start -->
| Инструмент | Версия |
|---|---|
| Node.js | 26.13.0 |
| npm | 12.2.1 |
| Git | 2.56.0 |
| Claude Code | 2.1.318 |
| elasticdump | 6.125.1 |
| kubectl | 1.37.2 |
| Helm | 4.3.1 |
| minikube | 1.39.0 |
| k9s | 0.51.0 |
| Gilt | 2.2.5 |
| devcontainer CLI (host/CI) | 0.90.0 |
<!-- tools:end -->

```text
images.json                         # версии CLI, Python image digests, семейства и бюджеты размера
requirements/common.in              # общие прямые Python-зависимости и исключения
requirements/ansible{10,12,14}.in    # разрешённые Ansible/core families
requirements/ansible{10,12,14}.txt   # полные точные locks с SHA256
.devcontainer/Dockerfile            # общий runtime и отдельная стадия сборки Git
.devcontainer/template.json         # общий шаблон настроек редактора и features
.devcontainer/ansible{10,12,14}/     # сгенерированные configs и отдельные feature locks
.devcontainer/devcontainer.json     # сгенерированная конфигурация по умолчанию (14)
.devcontainer/features/             # Node, Gilt и Claude Code/elasticdump
.devcontainer/tests/                # runtime, lock, cache, Gilt и Molecule tests
scripts/                            # обнаружение версий, resolver, генератор, build/test runner
compatibility/                      # проверяемые отчёты для следующего обновления
.github/workflow-templates/          # источники workflows; Actions versions из images.json
```

Генерируемые configs и workflows не редактируются вручную.
`python3 scripts/render.py --check` проверяет отсутствие рассинхронизации.
Внешние features закреплены отдельными `devcontainer-lock.json`; локальные
features закреплены самим git-коммитом и в этих lockfiles не перечисляются.

## Состав и размер

Один Python на образ, без системного `/usr/bin/python3`, pipx/uv/pyenv/conda,
NVM и других менеджеров версий. pip и npm остаются штатными установщиками
пакетов: они нужны для Python-библиотек и elasticdump. Corepack/Yarn/pnpm нет.

Node устанавливает локальная feature из официального архива с фиксированными
SHA256 для amd64/arm64. Gilt устанавливается официальным GitHub-бинарником,
так как опубликованный python-gilt 2.2.5 содержит некорректный wheel tag.
Git собирается в отдельной стадии; компилятор не копируется в runtime.
Claude Code и minikube сохранены. Claude использует один native-бинарник и
пользовательский launcher, глобальная команда — symlink.
Native Claude извлекается из официального платформенного npm-архива Anthropic
с зафиксированным SHA512 integrity; npm-wrapper и второй бинарник не устанавливаются.
Это устраняет зависимость сборки от меняющегося bootstrap и недоступного здесь
`downloads.claude.ai`. Updater закрепляет integrity отдельно для amd64/arm64.
Docker установлен только как CLI с Compose/Buildx; daemon используется с хоста.
Сокет автоматически подключает docker-outside-of-docker feature.

apt lists/archives и pip/npm download caches удаляются в том же слое `RUN`,
где создаются. Общая shell-обёртка очищает также сторонние features.
Проверка кешей выполняется на чистом образе до запуска инструментов:
работающие инструменты позже могут создать свои пользовательские кеши.

Размеры измеряются в несжатых байтах `docker image inspect`, отдельно для каждой
архитектуры. Порог `maxImageBytes` в `images.json` проверяется runner-ом;
его нельзя повышать автоматически при обновлении. Учёт слоёв отдельного образа
не равен дополнительному месту всех трёх образов: часть слоёв общая.
Старые образы, Docker build cache и пользовательские контейнеры автоматически
не удаляются. Общий `docker system prune` здесь не используется.

<!-- sizes:start -->
| Платформа | Образ | Несжатый размер | Проверено | Состояние lock |
|---|---|---|---|---|
| amd64 | 10 | 3,494,194,197 байт | 2026-11-04 | текущий |
| amd64 | 12 | 3,531,469,380 байт | 2026-11-04 | текущий |
| amd64 | 14 | 3,531,017,955 байт | 2026-11-04 | текущий |
<!-- sizes:end -->

## Сборка и тесты

Нужны Docker с Buildx, Python 3.10+ на хосте, Node/npm и devcontainer CLI версии
из `images.json`. На хосте скрипты используют стандартную библиотеку Python.
GNU Make нужен только для коротких команд ниже; можно запускать соответствующие
`python3 scripts/*.py` напрямую, как показано в Makefile.

```bash
npm install --global @devcontainers/cli@0.90.0
make check
make test                         # все три образа, сборка и проверки
make test VARIANTS=14             # один вариант
make build VARIANTS='10 12 14'     # только сборки
make record                       # сохранить результаты всех трёх успешных native-прогонов
```

Если CLI отсутствует в PATH, задайте `DEVCONTAINER_CLI=/полный/путь/devcontainer`.
Образы получают локальные теги `ansible-infra:ansible10-local` и аналогичные.
Для VS Code выберите конфигурацию Ansible 10/12/14 через Reopen in Container.
Эквивалент явного запуска:

```bash
devcontainer up --workspace-folder . --config .devcontainer/ansible12/devcontainer.json
```

Проверяется точное совпадение всех установленных Python-пакетов с lockfile,
`pip check`, отсутствие лишних runtime/managers/compiler/daemon, пустота кешей,
CLI-команды, импорты библиотек, yq, bcrypt/Vault, ansible-lint/playbook, Gilt overlay.
Molecule выполняет create → converge → idempotence → verify → destroy от `vscode`
через Docker хоста. Имена его узлов уникальны для прогона.
Runner удаляет только собственные временные контейнеры с уникальной меткой.

Полные тесты запускаются на native-архитектуре. CI содержит независимые jobs
для amd64 и arm64; наличие arm64 в workflow само по себе не означает успешный
локальный arm64-прогон. Фактически проверенные платформы перечисляет validation.json.
Логи каждого этапа и данные о размере записываются в `.build/<arch>/`.

## Следующее обновление

```bash
make audit       # только свежие данные в .build/, исходники не меняются
make update      # обновить metadata/configs/workflows, pip locks и feature locks
make check
make test
make record
git diff --check
git diff         # просмотреть версии, исключения, размеры и generated files перед коммитом
```

Updater проверяет официальные реестры Python/Node/PyPI/npm, GitHub Releases,
kernel.org и Kubernetes stable.txt; prerelease Node не выбирается. Python base
фиксируется по patch-тегу и multiarch digest. Для каждого варианта pip resolver
работает в его собственном Python, без установки менеджеров в конечный образ.
Все non-yanked SHA256 артефактов каждой выбранной версии попадают в lock, что
позволяет устанавливать amd64/arm64 wheels. `--require-hashes` включён при сборке.
Для релизного локального обновления используйте `make test BUILD_FLAGS=--no-cache`,
чтобы освежить также apt-пакеты и build dependencies, даже если Python/CLI pins
не изменились. Обычные повторные проверки используют кеш. В CI каждый native
runner начинает без нашего кеша образов и устанавливает свежие apt-пакеты.
Отдельные исходные sdist могут потребовать build-зависимости: финальная сборка
и runtime-тесты обязательны даже после успешного dry-run resolver.

Таблицы совместимости и размеров обновляет `render.py`: версии из resolved.json,
а размеры из validation.json. Если lock изменился после замера, таблица явно
помечает прежний результат как предыдущее окружение.

При добавлении нового Ansible сначала обновите контроллер/target ranges по
официальной матрице и `FAMILIES` в updater; не повышайте Python за границу
поддержки core. После обновления проверьте таблицу README и причины отставания
от latest в compatibility/packages.json. Проверьте новые ограничения пакетов,
изменения синтаксиса CLI и release notes. Не обходите конфликт через `--no-deps`.

CI `build.yml` на main/PR/ручном запуске собирает и тестирует матрицу 3×2,
сохраняет сводку результата и размеры артефактами, без входа в registry и публикации.
CI `update.yml` раз в неделю или вручную рассчитывает обновление и отдаёт
`update.patch`, latest releases и compatibility reports как review-артефакт.
Он не создаёт коммит, PR и не пушит изменения. После применения patch нужно
запустить полную сборку/тесты; сам update workflow её не заменяет.
Renovate отключён, чтобы не было второй независимой автоматики изменения pins.
Экспорт CI ограничен явным списком файлов в `scripts/artifacts.py`; весь `.build`
и скрытые файлы не загружаются. Полные логи остаются локально, при ошибке последние
80 строк выводятся в обычный CI log.

## Особенности runtime

Upstream passlib 1.7.4 может вывести сообщение об отсутствии `bcrypt.__about__`;
это известная диагностика старого passlib с современным bcrypt 4.x.
Проверки хеширования и Ansible-фильтра должны всё равно успешно пройти.
Включать bcrypt 5 или подавлять реальные ошибки ради зелёной сборки нельзя.
Hashicorp mirror не включается обновлятором.
