# Claude Code и elasticdump

Локальная feature поддерживает Linux amd64 и arm64. Версии и SHA512 integrity
официальных платформенных npm-архивов Claude Code задаются в `images.json`;
`scripts/render.py` переносит их в конфигурации вариантов.

Установщик проверяет SHA512 архива до распаковки и запуска. Один native-бинарник
Claude находится в `~/.local/share/claude/versions` и принадлежит пользователю
devcontainer. `~/.local/bin/claude` и `/usr/local/bin/claude` ссылаются на него.

Elasticdump устанавливается npm-приложением в `/usr/local/share/elasticdump`.
Точные overrides `ip-address` и `form-data@<3` обновляются общим updater;
семейство form-data 2.x сохраняет API legacy request внутри requestretry.
`package.json` и `package-lock.json` сохраняют установленное дерево.
Кеш npm и временные архивы удаляются в том же слое.

Требуются common-utils с созданным пользователем, curl и Node.js/npm.
Полная проверка: `make test`. Runtime smoke проверяет реальный SOCKS5 IPv6
handshake и защиту multipart от CRLF-инъекции; отдельный тест проверяет отказ
при испорченном архиве Claude без замены установленного бинарника.
