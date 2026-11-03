# Claude Code и elasticdump

Локальная feature использует официальный native installer Claude Code и npm
для elasticdump. Установщик загружается с официального Google CDN Claude Code,
как в исходной devcontainers-extra feature. Версии задаются через `claudeVersion` и `elasticdumpVersion`.

Claude устанавливается от пользователя devcontainer. `/usr/local/bin/claude`
ссылается на его штатный `~/.local/bin/claude`, поэтому нет второй копии бинарника,
а механизм автообновления launcher сохраняется. Кеш npm удаляется в том же слое,
в котором устанавливается elasticdump.

Требуются common-utils с созданным пользователем, curl и Node.js/npm.
