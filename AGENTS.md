# Работа с Ansible devcontainers

Пользователь запретил любые push. Не выполнять `git push`, публикацию Docker
образов, создание PR или workflow с записью в репозиторий. Итог работы —
локальный коммит после успешной проверки и показа diff пользователю.
Это разрешение на локальные изменения/сборки/тесты, отдельное подтверждение
на каждую обратимую правку не требуется.

## Источники и структура

- Одна main, три варианта Ansible 10/12/14. Не заводить ветку на каждый вариант.
- Источники: images.json, requirements/*.in, .devcontainer/template.json,
  .github/workflow-templates/*.yml и локальные features.
- Генерируемые configs/workflows: `python3 scripts/render.py`. Проверка: `make check`.
- Python locks: `scripts/update.py --write --resolve --features`, затем
  `scripts/audit.py --write`. Не переписывать вручную сотни hash pins.
- Python controller ceilings: 10→3.12/core2.17, 12→3.13/core2.19,
  14→3.14/core2.21. Перепроверять по upstream support matrix, не только Requires-Python.
- All stable direct packages should be as new as the complete resolver permits.
  bcrypt<5 остаётся обоснованным passlib 1.7.4, пока реальный тест не докажет исправление.

## Обязательные инварианты

- Один Python в каждом конечном образе. Никаких NVM/fnm/Volta/asdf/mise,
  pyenv/uv/conda/pipx и других runtime/version managers. pip/npm разрешены.
- Node напрямую из официального архива с точной версией и SHA256. Нет Corepack/Yarn/pnpm.
- Сохранить Claude Code и minikube. Claude native-бинарник в одном экземпляре.
- Docker CLI + daemon хоста. Не добавлять dockerd, systemd и компиляторы в runtime.
- Очищать apt/pip/npm и временные загрузки в создавшем их RUN, а не поздним слоем.
- Не отключать pip dependency checks/hashes. Не чинить wheel metadata sed-ом.
- Feature locks фиксировать и собирать с `--frozen-lockfile`.
- Не повышать budgets размера автоматически ради прохождения CI. Сначала объяснить рост.
- Не удалять пользовательские образы/контейнеры/volumes и не делать глобальный prune.

## Цикл обновления

1. Прочитать README, images.json, compatibility/*.json и текущее git status.
2. `make audit`, изучить upstream release notes и совместимость каждого варианта.
3. `make update`; проверить metadata, lockfiles, generated CI и diff.
4. `make check`; `make test BUILD_FLAGS=--no-cache` для релизного обновления
   (или кешированная повторная проверка неизменившихся слоёв) на native amd64, затем native arm64 в доступном
   окружении/CI. Не выдавать один amd64-прогон за multiarch-проверку.
5. `make record` после всех трёх успешных локальных вариантов; проверить
   сгенерированные README matrix/sizes, compatibility reports и заметки об исключениях.
6. Показать полный diff перед локальным коммитом. После коммита проверить чистоту.
   Никаких push.

Runner пишет логи в .build/<arch>. Test result должен включать hash-lock match,
pip check, cache/runtime audit, CLI smoke, Gilt и Molecule lifecycle через Docker
хоста от vscode. После изменения критической логики выполнить соответствующие
проверки заново; не повторять дорогостоящие неизменившиеся сборки без причины.

В update workflow результат — только patch/reports artifact. Применение patch
требует дальнейших build/tests; workflow не должен самостоятельно коммитить/пушить.
