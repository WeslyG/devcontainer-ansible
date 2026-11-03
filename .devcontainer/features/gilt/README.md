# Gilt

Локальная devcontainer feature устанавливает официальный бинарник
[Gilt](https://github.com/retr0h/gilt/releases) в `/usr/local/bin/gilt`.
Поддерживаются Linux amd64 и arm64. Установка выполняется от root;
бинарник доступен всем пользователям контейнера.

```json
"features": {
  "./features/gilt": {
    "version": "2.2.5"
  }
}
```

Для обновления измените `version` в `.devcontainer/devcontainer.json` на точную
версию релиза. `latest` не поддерживается, чтобы версия не менялась незаметно.
Установщик скачивает соответствующий архитектуре бинарник и `checksums.txt`
из одного GitHub Release и проверяет SHA256 **до** установки и запуска.
При отсутствии checksum или несовпадении хеша сборка прерывается.

Требуются bash, curl, ca-certificates и стандартные GNU coreutils.
На Debian/Ubuntu отсутствующие curl и CA-сертификаты устанавливаются через apt.
Go и Python для установки Gilt не нужны.

Feature хранится в Git вместе с devcontainer и не требует публикации в GHCR.
Локальные features не получают OCI-запись в `devcontainer-lock.json`:
их код фиксируется коммитом, версия Gilt — параметром `version`.

Проверка установщика в отдельном чистом контейнере:

```sh
docker run --rm --platform linux/amd64 \
  -v "$PWD/.devcontainer/features/gilt:/feature:ro" \
  -v "$PWD/.devcontainer/tests:/tests:ro" \
  python:3.12-trixie bash /tests/gilt.sh
```

Для ARM64 замените платформу на `linux/arm64`. Тест устанавливает настоящий
релиз, проверяет запуск и overlay локального Git-репозитория по commit SHA,
затем проверяет отказ при испорченном бинарнике,
отсутствующем checksum и нефиксированной версии. Запускайте его в одноразовом
контейнере: установщик пишет в `/usr/local/bin`.
