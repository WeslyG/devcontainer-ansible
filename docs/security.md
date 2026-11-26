# Безопасность образов

Каждый native-образ проходит функциональные тесты перед публикацией.
Отдельная опциональная job `scan-published` запускается после успешного
multiarch publish и проверяет все шесть native-образов по digest из проверенных
отчётов публикации. Сканирование не блокирует push. High/Critical вне адресных
исключений Ansible 10 и ошибки сканера делают статус этой job неуспешным.
Все три варианта каждой архитектуры сканируются даже при находках в одном.

Ручной workflow input `scan_published` включён по умолчанию. Для push в main
скан выключается repository variable `SCAN_PUBLISHED_IMAGES=false`.
Artifacts `security-<release>-<arch>-attempt<N>` содержат полный JSON Trivy,
CycloneDX SBOM, разбор политики, время скана, Git SHA, native digest, версию
и pinned image сканера, metadata и SHA256 базы CVE. База фиксируется на один
прогон архитектуры; JSON отражает её состояние при этом прогоне после сборки.
Срок хранения равен Actions retention репозитория; для длительного архива
скачать artifact до истечения срока. Повтор job создаёт отдельный artifact.

Локально после `make test VARIANTS=10`:

```sh
make security VARIANT=10 ARCH=amd64
```

Отчёты: `.build/<arch>/trivy-<variant>.json`, `security-<variant>.json`,
`sbom-<variant>.cdx.json`. В CI отдельные post-publication отчёты находятся в security artifacts.

## Принятый риск Ansible 10

Для совместимости требуется Ansible 10/core 2.17. В `scripts/security.py`
приняты CVE-2025-14010 для PyPI ansible и CVE-2026-11332 для PyPI ansible-core
только в варианте 10. Находки остаются в отчёте с причиной исключения.
Другие CVE, пакеты и варианты проверяются полностью. Новый advisory требует
отдельного разбора и явного изменения политики.

## Разбор находок

Сверять установленную версию, путь, архитектуру, upstream advisory и Debian
Security Tracker. Debian backports не определяются сравнением upstream-версий.
Встроенный SBOM может перечислять зависимости сборки, отсутствующие в runtime;
такие совпадения нужно подтверждать файлами и связями компонентов. Исключения
по всему пакету, severity и наличию исправления не применяются.

Обновление: `make update`, `make check`, native build/tests, затем `make security`
для каждого варианта/архитектуры. Сравнить полный отчёт, проверить размер образа
и работу инструментов. Сохранить dig/nslookup/host, Claude Code и minikube.
Не удалять metadata/SBOM и не менять имена пакетов ради чистого отчёта.

DNS-клиенты dig/nslookup/host собираются из BIND 9.20 ESV с `--without-lmdb`.
BIND-библиотеки находятся в `/usr/local/lib/ansible-dns` с сохранением dynamic linking; LMDB и DNS-сервер не устанавливаются.
Исходник закреплён версией и SHA256; локальный DNS-тест проверяет все три клиента.

Gilt собирается из закреплённого тега исходников с проверкой SHA256. Временный
Go toolchain закреплён версией и SHA256 для обеих архитектур; GOTOOLCHAIN=local
запрещает автоматическую установку других toolchains. Обновляются x/crypto и
x/text, выполняются upstream-тесты и go mod verify. Go и его caches удаляются
в том же RUN; go.mod/go.sum сохраняются в /usr/local/share/gilt.

Updater обновляет BIND в поддерживаемой ESV-ветке 9.20, версии/хеши Go и
исходников Gilt, x/crypto, x/text и digest Trivy. На хосте нужен curl для
загрузки metadata и проверки новых исходников; в runtime Go не устанавливается.

В чистом образе проверяются дубликаты команд по inode/реальному файлу и
повторные Python distributions. Симлинки usrmerge и CLI aliases допустимы.
Python bytecode compilation отключена; __pycache__, apt/pip/npm и build caches
удаляются при сборке. Размер проверяется до функциональных тестов; лимит
не повышается автоматически. Анализировать также docker history и размеры
крупнейших каталогов, поскольку удаление файла в следующем слое не уменьшает
уже сохранённый слой.

Node runtime устанавливается без C/C++ headers из архива. Native addons требуют
отдельного build-окружения; Node/npm/npx сохраняются.

Локальная feature Gilt/EditorConfig использует общий временный Go toolchain.
EditorConfig checker устанавливается из официального source release без
PyPI-обёртки. Команды ec и editorconfig-checker указывают на один бинарник;
upstream-тесты обоих проектов выполняются перед установкой.

Kubernetes feature использует source-built kubectl/minikube общего Go builder
и официальный Helm archive, проверяя версии и SHA256 из images.json. Загрузки имеют timeout/retry, архивы
удаляются в том же RUN. Updater получает версии и checksum обеих архитектур.

OpenSSH client собирается из официального portable release. Version/SHA256
находятся в images.json и обновляются updater. Собственный deb использует
Debian epoch 1, предотвращая замену клиента старым пакетом при apt upgrade.
SSH-сервер не устанавливается; проверяются версия, keygen и разбор конфигурации.

Сборка Gilt/EditorConfig выполняется общей builder-стадией для всех Python
вариантов. В runtime копируются только CLI, aliases и metadata/лицензии.
Локальная feature сверяет pins (включая свой script hash) и SHA256 бинарников;
при отсутствии подходящего prebuilt-набора она собирает их из исходников.
Временные файлы очищаются в создающем RUN, timestamps общего артефакта
нормализованы для переиспользования registry layers.

Общий Go builder также собирает K9s, minikube и kubectl с точными версиями
исправленных транзитивных модулей из tools.goSecurityModules. Для kubectl
используются официальный main.go с SHA256 и опубликованные Go-модули той же
версии Kubernetes. K9s/minikube используют source archives с SHA256.
Версии проектов и hashes обнаруживает updater; Go проверяет module checksums.
Сохраняются go.mod/go.sum и список импортируемых пакетов каждого CLI.
Supplemental CycloneDX SBOM указывает точные версии source projects, поскольку
локальная сборка Go может обозначать main module как devel.

K9s/containerd resolver сохраняет совместимость Kubernetes SDK: выбирается
последний patch максимальной совместимой containerd-серии. Причина и выбранный
override записаны в manifest. Применяются исходные тесты K9s config/cmd и
minikube config. Даты native Go CLI берутся из исходников/module metadata,
поэтому обновление Python само по себе не пересобирает этот общий слой.
Go module/build caches используют BuildKit cache mounts только на сборщике;
они не входят в image layers и не копируются в runtime.

Elasticdump устанавливается как отдельное npm application в
/usr/local/share/elasticdump с точным override ip-address. package.json и
package-lock.json сохраняют фактическое дерево зависимостей; updater обновляет
security pin. SOCKS5 IPv6 проверяется локальным handshake-тестом. Rootless
networking slirp4netns/libslirp0 не устанавливается в итоговом CLI-only образе.

## Сопоставление source builds с Debian CVE

Custom deb сохраняет имя пакета и точную upstream-версию. Trivy использует
Debian advisories, где stable-ветка может иметь статус unfixed даже для source
build более новой upstream-версии. Сырые результаты сохраняются без подавления;
такие строки требуют сверки с источником исправления.

| Пакет | Версия source build | Проверяемые CVE | Источник исправления |
| --- | --- | --- | --- |
| Git | 2.56.1 | CVE-2026-105437, CVE-2026-111760, CVE-2026-114466 | [Git security release](https://github.blog/open-source/git/git-security-vulnerabilities-announced-7/) |
| OpenSSH client | 10.6p2 | CVE-2026-60002 | [Debian: исправлено в 10.4p1](https://security-tracker.debian.org/tracker/CVE-2026-60002) |
| OpenSSH client | 10.6p2 | CVE-2026-106583 | [Debian: затронуты версии до 10.6](https://security-tracker.debian.org/tracker/CVE-2026-106583) |

CVE-2026-59999, CVE-2026-60000, CVE-2026-106553 и CVE-2026-106555
относятся к sshd; сервер отсутствует, а upstream-версия клиента также содержит
исправления. См. [OpenSSH release notes](https://www.openssh.org/releasenotes.html).
Это описание подтверждённых исправлений, а не правило автоматического
исключения пакета из скана. Для новой версии сверять таблицу с advisory.

Наличие нефильтрованных CVE без исправления в Debian не означает, что сборка
может автоматически устранить их обновлением apt. Не понижать severity и не
исключать такие находки только по признакам no-dsa/not-fixed. Отдельная job
сканирования показывает их для разбора; успешный build означает прохождение
функциональных тестов и проверок размера/кешей, а не нулевое число CVE.

Go upstream tests и бинарники используют одинаковый `-trimpath`, чтобы
переиспользовать compiler cache и исключить временные build paths из бинарников.

## Advisory для вложенных компонентов

Node.js 26.13.1 включает исправление CVE-2026-111497 из security release
26.12.1. Для bundled Brotli проверять Node release и patch provenance, поскольку
версия библиотеки сама по себе не описывает backports.
Источник: [Node security release](https://nodejs.org/en/blog/vulnerability/october-2026-security-releases).

CVE-2026-41567 и CVE-2026-42306 описывают обработку archive/mount в Docker
daemon. Образ содержит Docker CLI без dockerd; при разборе находок в SDK
minikube/Buildx нужно также проверять импортируемые Go packages и daemon хоста.
Upstream указывает исправление Docker Engine 29.5.1:
[archive execution](https://github.com/moby/moby/security/advisories/GHSA-x86f-5xw2-fm2r),
[mount race](https://github.com/moby/moby/security/advisories/GHSA-rg2x-37c3-w2rh).
Эти строки остаются в сыром отчёте; версия клиентского SDK не доказывает
наличие уязвимого daemon в devcontainer.

Бинарники общих Go CLI и их metadata копируются раздельными слоями;
изменение pins metadata сохраняет возможность повторно использовать binary layer.

Minikube использует upstream Linux flags: CGO_ENABLED=1 и libvirt_dlopen.
Это сохраняет KVM driver без обязательной линковки libvirt.so. Runtime
зависимости проверяются через ldd; компилятор и Go SDK остаются в builder.
Остальные Go CLI собираются с CGO_ENABLED=0. Go flags сбрасываются для каждого
проекта, включая go list inventory, чтобы inventory соответствовал бинарнику.

Elasticdump использует совместимый `form-data` 2.x для legacy request и актуальный 4.x для собственных запросов. Версия 2.5.6 закрывает CVE-2025-7783 и CVE-2026-12143; smoke проверяет фактический resolver request и экранирование CRLF в multipart. Pin и выбор последнего стабильного patch семейства 2.x входят в общий updater.

CVE-2026-17106 касается распаковки tar в moby/go-archive: Unpack, Untar и
ApplyLayer. CVE-2026-78661 относится к функциям Parse/ParseFragment HTML-парсера
golang.org/x/net/html. Наличие версии всего Go-модуля в build metadata ещё не
устанавливает наличие и достижимость этих функций. При разборе SDK сверять
импорты, символы бинарника и вызовы затронутых функций; без доказательства
находка остаётся в отчёте и не исключается политикой.
Источники: [go-archive advisory](https://github.com/moby/go-archive/security/advisories/GHSA-hfg8-hc9c-6c3h),
[Go HTML parser advisory](https://pkg.go.dev/vuln/GO-2026-6860).
