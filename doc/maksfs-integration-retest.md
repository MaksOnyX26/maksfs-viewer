# Повторная тестовая сборка после C2664

Подготовлено 2026-11-11 в Codex Cloud. Windows-сборка не запускалась.

- Новая ветка: `codex/integration-windows-retest-20261111`.
- Основа ветки: `codex/integration-windows-test-20261110` @
  `f619dd93e2be2c55dd45f61f849e534e846ad07d`.
- Точный **source SHA**: `c90b41cc62ef16e21bcb581b62f7f248d991c144`.
- Исправление PR #3 включено fast-forward только в новую ветку. Исходный PR
  остаётся Draft, merge через GitHub не выполнялся. Прежняя тестовая ветка,
  maksfs-main и PR #1/#2/#3 не изменялись.

В `llstatusbar.cpp:635` проверена замена
`setText(clock)` на `setText(LLStringExplicit(clock))`, устраняющая запрет
неявного преобразования char[16] через explicit-конструктор. Дополнительных
изменений C++ нет.

## Workflow и происхождение пакетов

Файл `.github/workflows/maksfs-build-windows.yml` унаследован от тестовой ветки.
Изменены только три строки: допущенная ветка, SOURCE_SHA и первый checkout ref.
SOURCE_SHA и checkout закреплены на полном SHA исправления выше.

Сохранены manual-only `workflow_dispatch`, обязательный Boolean confirm_build
с default=false, условие confirm_build=true и run_attempt==1, read-only
permissions и отсутствие автоматической сборки при push/PR. Job допускается
только для `codex/integration-windows-retest-20261111`.

Компилятор получает чистый checkout source SHA. Packaging controls после
компиляции берутся из workflow SHA (`github.sha`), который отличается от source
SHA и отдельно записывается в provenance. Скрипты упаковки не изменялись:
проверяются фактический checkout/source SHA, текущие run ID/workflow SHA и
fresh_compile. Сохраняются свежий binary checkpoint до упаковки, затем Setup
EXE, Portable ZIP, manifest файлов, сведения о комплектности и SHA256.
Старые snapshots из maksfs-main не скачиваются. Имена артефактов включают новый
run ID, сохраняется 30-дневный срок хранения. GitHub Releases не создаются.

## Лёгкие проверки

- `git diff --check` — успешно.
- YAML активных workflow разобран; для build проверены manual-only/default=false,
  ветка, source SHA/checkout, один compile, отсутствие download-artifact и
  сохранение checkpoint раньше staging.
- Python syntax packaging scripts и fixture-проверки snapshot/provenance:
  успешный свежий snapshot, отказ при другом checkout SHA; package отказывает
  при старом source SHA, другом run ID/workflow SHA, fresh_compile=false
  и отсутствии обязательного EXE. Проверки прошли.
- Изолированный Linux C++20 harness с реальными определениями строковых типов
  и сигнатурами setText/setToolTip: `-Wall -Wextra -Werror`, успешные компиляция
  и выполнение проверок текста/tooltip/кэша/выключенных часов. Исходный вызов
  с char[16] воспроизводимо отвергнут компилятором.
- C++ и packaging tree совпадают с source SHA; единственное последующее
  изменение кода workflow — три указанные строки.

Проверки не заменяют MSVC, PowerShell/NSIS, сборку viewer или интерактивный
тест Windows 11. Windows 11, Second Life и OpenSim не объявляются проверенными.

## Ручной запуск владельцем

1. Открыть [Actions workflow](https://github.com/MaksOnyX26/maksfs-viewer/actions/workflows/maksfs-build-windows.yml).
   В default branch он может называться **MaksFS first Windows build**;
   в новой ветке — **MaksFS integration Windows x64 test**.
2. Нажать **Run workflow** и обязательно выбрать ветку
   **codex/integration-windows-retest-20261111**.
3. Включить **confirm_build** и нажать **Run workflow** один раз.
4. Проверить Source в identity.txt/summary:
   `c90b41cc62ef16e21bcb581b62f7f248d991c144`.
   Workflow SHA должен совпадать с head новой ветки при dispatch.

Эквивалент из авторизованного CLI владельца:

```sh
gh workflow run maksfs-build-windows.yml --repo MaksOnyX26/maksfs-viewer \
  --ref codex/integration-windows-retest-20261111 -f confirm_build=true
```

Не выбирать старую тестовую ветку или maksfs-main: там остаются прежние
workflow/source SHA. Повторный запуск существующего failed run также не
использует новый workflow. Если новая сборка закончится ошибкой упаковки,
сначала проверить сохранённый свежий checkpoint, не повторять компиляцию
и не подменять binaries старой сборкой из main.
