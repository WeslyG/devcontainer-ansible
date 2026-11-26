# Gilt, EditorConfig checker и общие Go CLI

Локальная feature поддерживает Linux amd64 и arm64. Общая стадия Dockerfile
собирает Gilt, EditorConfig checker, K9s, minikube и kubectl из закреплённых
официальных исходников. Версии, SHA256 исходников, Go SDK для обеих архитектур
и совместимые security updates модулей находятся в `images.json`.
`scripts/update.py` обновляет pins; `scripts/render.py` генерирует конфигурации
и metadata исходников.

Перед сборкой проверяются SHA256 архивов и `go mod verify`, выполняются
upstream-тесты. `GOTOOLCHAIN=local` запрещает автоматическую загрузку другого
Go toolchain. Minikube использует upstream Linux flags `CGO_ENABLED=1` и
`libvirt_dlopen`; остальные Go CLI собираются с `CGO_ENABLED=0`.

Runtime получает только бинарники, лицензии, go.mod/go.sum, список импортов
и supplemental CycloneDX SBOM. `ec` и `editorconfig-checker` — aliases одного
бинарника. Go SDK, исходники и caches в runtime отсутствуют.

Feature проверяет fingerprint pins/установщиков и SHA256 каждого готового
бинарника. Совпадающий набор общего builder используется без компиляции.
При отсутствии подходящего набора feature собирает инструменты временным
checksum-pinned SDK и удаляет временное окружение в создающем RUN.

Локальный код фиксируется git-коммитом; OCI feature lock для него не создаётся.
Полная проверка: `make test` на native-платформе. CI выполняет тот же прогон
на amd64 и arm64. Тесты проверяют CLI, Gilt overlay локального Git-репозитория
по commit SHA, точные версии и отказ при повреждённых исходниках без замены
установленного Gilt. Полный цикл обновления описан в корневом `AGENTS.md`.
