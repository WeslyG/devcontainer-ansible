# Сопровождение Ansible devcontainers

## Источники и структура

- Ветка main содержит варианты Ansible 10/12/14 из общего Dockerfile и features.
- Источники: images.json, requirements/*.in, .devcontainer/template.json,
  .github/workflow-templates/*.yml и локальные features.
- Генерация configs/workflows/таблиц: `python3 scripts/render.py`; проверка: `make check`.
- Python locks: `scripts/update.py --write --resolve --features`, затем
  `scripts/audit.py --write`. Hash pins генерируются из PyPI metadata.
- Семейства: 10→Python3.12/core2.17, 12→Python3.13/core2.19, 14→Python3.14/core2.21.
  Границы controller/target Python определяются официальной support matrix Ansible.
- Прямые и транзитивные зависимости выбираются максимально свежими в пределах
  совместимости. bcrypt<5 закрепляет проверенную совместимость backend passlib.

## Инварианты runtime

- Один Python на образ. NVM/fnm/Volta/asdf/mise, pyenv/uv/conda/pipx отсутствуют.
  pip/npm используются как установщики пакетов; Corepack/Yarn/pnpm отсутствуют.
- Node устанавливается официальным архивом с точной версией и SHA256 для обеих архитектур.
- Claude Code имеет один native-бинарник, принадлежащий vscode; minikube включён.
- Docker CLI работает с daemon хоста. Компиляторы Git/OpenSSH/BIND остаются в builder stages.
- Общий Go builder собирает Gilt/EditorConfig/K9s/minikube/kubectl; SDK отсутствует в runtime.
- При обновлении minikube сверять Makefile: ISO_VERSION, STORAGE_PROVISIONER_TAG,
  CGO_ENABLED=1 и libvirt_dlopen. Проверить ldd: без missing libraries/libvirt.so.
- Git/OpenSSH регистрируются как deb с epoch 1, чтобы apt не устанавливал вторую копию.
- DNS-клиенты BIND собираются без LMDB; dig/nslookup/host обязательны.
- apt/pip/npm caches и временные загрузки очищаются в создающем их RUN.
- Python dependencies проверяются через hash-lock и pip check; features — frozen-lockfile.
- Бюджеты размера требуют явного анализа перед изменением.
- Пользовательские контейнеры, образы, volumes и общий build cache сохраняются.
  Временные ресурсы тестов удаляются только по собственным уникальным меткам.

## Цикл обновления

1. Прочитать README, images.json, compatibility/*.json и git status.
2. `make audit`: изучить выпуски и совместимость вариантов.
3. `make update`: обновить manifest, locks, configs/workflows и отчёты.
4. `make check`; выполнить native build/tests. Для релизного обновления:
   `make test BUILD_FLAGS=--no-cache`. Локальные amd64 и arm64 результаты
   учитываются отдельно; CI проверяет обе архитектуры native runners.
5. `make record` после успешного полного прогона трёх вариантов. Проверить размеры,
   README matrix и причины ограничений в compatibility/packages.json.
6. Показать полный diff перед коммитом; проверить чистоту после коммита.
   Git commit/push выполнять в рамках запроса пользователя.

Runner пишет .build/<arch>: результаты включают hash-lock, pip check, аудит
кешей/менеджеров, CLI smoke, Gilt, Testinfra и Molecule lifecycle от vscode
через daemon хоста. Проверять изменённую критическую логику; существующие
успешные тесты неизменившихся компонентов не требуют повторения без причины.

## Релизы Docker Hub

- Версия генерируется scripts/version.py: Asia/Yekaterinburg, YYYY.MM.DD,
  повторные выпуски -1/-2. Python версии хранятся в dependency manifest.
- Один PLATFORM_VERSION на всю матрицу. ENV, /etc/platform_version, OCI version
  label, image tags и отчёты должны согласовываться.
- CI учитывает опубликованные native- и multiarch-теги. Concurrency сериализует
  выпуск main целиком; cancel-in-progress=false.
- build.yml на main собирает и тестирует 3×2 native-матрицу. После тестов job
  публикует точный проверенный image ID под `<arch>-ansible<major>-<version>`.
- На одноразовых CI runners Go builder выполняется перед runtime build; затем
  удаляются только exec.cachemount текущего отдельного Buildx builder. Immutable
  результат Go stage сохраняется. Этот prune не переносить в локальный цикл
  обновления: его compiler/module caches нужны для повторных сборок.
- Job publish зависит от успеха всей матрицы. Он проверяет шесть отчётов и
  публикует `weslyg/ansible-infra:ansible<major>-<version>` по точным digest.
  Манифесты должны содержать ровно linux/amd64 и linux/arm64.
- Publication разрешена push/ручному запуску main; PR и другие ветки тестируются.
  Secrets: DOCKERHUB_USERNAME и DOCKERHUB_TOKEN либо DOCKERHUB_PASSWORD.
- Занятые теги с другим содержимым сохраняются; публикация завершается ошибкой.
  Идентичные теги допускают повтор job. Локальные build/test команды не публикуют образы.
- Actions versions закреплены в images.json и включены в общий updater.
- CI экспортирует только явно перечисленные публичные файлы. Credentials,
  скрытые файлы и каталоги целиком в artifacts не включать.

Update workflow выдаёт patch/reports для проверки. Применённое обновление
проходит build/tests и стандартный процесс коммита/публикации.

## Проверка безопасности

Правила и команды: docs/security.md. После публикации отдельная опциональная
job scan-published сканирует точные native digest и сохраняет снимки JSON/SBOM,
сканера и базы CVE. Сканы не блокируют публикацию; их собственный статус должен
показывать ошибки и High/Critical вне адресных исключений Ansible 10.
Ручной флаг scan_published и repository variable SCAN_PUBLISHED_IMAGES управляют
запуском. Сохранять отдельный artifact для каждого run_attempt; экспортировать
только явный список публичных файлов. Локально scripts/security.py проверяет
точный tested image ID. Нельзя обещать отсутствие CVE по одному статусу сборки.

Тестовый harness запускает готовый image ID с исходными runtime-настройками devcontainer и UID пользователя образа. Перед smoke/Molecule проверяется совпадение `.Image` контейнера с измеренным image ID. Временная конфигурация запуска находится в `.build/<arch>/runtime-<variant>/devcontainer.json`.

## Badges уязвимостей

Генератор `scripts/badges.py` использует готовые scan-metadata.json текущего CI
run. Проверять release/revision/run ID, выбирать последнюю попытку отдельно
для amd64/arm64; ошибку сканера показывать серым. Счётчик High/Critical следует
адресной политике Ansible 10. `compatibility/security-snapshot.json` и блок
security-badges README обновляются вместе. Job badges получает contents:write;
в git add явно перечислены только README и снимок. Коммит содержит `[skip ci]`;
новый build/scan не нужен.
Локальная перегенерация: `python3 scripts/badges.py`. При изменении документации
по запросу без новой сборки использовать `[skip ci]` и проверить отсутствие
нового workflow run на опубликованном SHA.
