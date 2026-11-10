# MaksFS: одна тестовая сборка интеграции для Windows x64

Подготовлено 2026-11-10 в Codex Cloud.
Ветка управления: `codex/integration-windows-test-20261110`, создана от
`07f4f3f7fc83f36fae586de0a21d9c051f2832ab`.
Проверка совместимости PR #1/#2 повторно не проводилась.

## Что подготовлено

Существующий `.github/workflows/maksfs-build-windows.yml` адаптирован только
в новой ветке. Он запускается вручную с `confirm_build=true`, только на этой
ветке и только при `run_attempt == 1`. Автоматических push/PR запусков нет.
Повторный запуск jobs не повторяет компиляцию. Сохранены read-only permissions,
стандартный windows-2022, прежние инструменты/профиль ReleaseFS_open и лимиты
отдельных стадий. Общий предел увеличен со 150 до 180 минут для упаковки;
это максимум, а не оценка длительности. Подписи и GitHub Releases нет.

Компилируются исходники **ровно** коммита
`07f4f3f7fc83f36fae586de0a21d9c051f2832ab`, а не head новой ветки.
Checkout проверяется по Git SHA и чистоте до компиляции. Workflow SHA отдельно
фиксируется как `GITHUB_SHA`/`WORKFLOW_SHA`. Только после компиляции получаются
packaging scripts из workflow-коммита и копируются поверх `ci/packaging/*.py`;
исходники viewer и его брендинг не меняются. Скрипты build/configure/stage и
полный upstream packaging manifest используются существующие.

Старый `maksfs-package-windows.yml` не запускается: он выбирает snapshots из
`maksfs-main`. Нет `download-artifact`, кэша или пути использования старой сборки.
Snapshot содержит **новые** EXE/DLL и зависимости текущего job. Он сохраняется
до NSIS/staging, чтобы ошибка упаковки не требовала повторной компиляции.

## Происхождение и проверки пакетов

`snapshot.py` проверяет фактический checkout SHA и записывает source SHA,
workflow SHA, run ID/URL/attempt, профиль и fresh_compile=true в
`packaging-inputs.json`. Удалена ссылка на старый successful run, которая могла
создавать ложное впечатление использования старой сборки.

`package.py` отказывает при несовпадении source SHA, run ID, workflow SHA или
fresh_compile. Копия `BUILD-PROVENANCE.json` попадает в staged tree, Portable ZIP,
Setup EXE и file manifest с SHA256.

Существующая упаковка сохраняет resources, shaders, skins, character/fonts,
CEF/VLC, WebRTC, app-local VC++ runtime и уведомления о лицензиях; проверяет
обязательные файлы, core x64 PE architecture и прямые DLL imports. Delay imports
записываются в отчёт; динамическая загрузка и работоспособность зависимостей на
Windows 11 требуют runtime-тестов. Собираются per-user unsigned NSIS Setup и
Portable ZIP. Проверяются CRC/число файлов и SHA256 содержимого ZIP, затем
silent install в путь с пробелами, SHA256 всех установленных файлов и удаление
только упакованных файлов с сохранением пользовательского sentinel-файла.
Это тест упаковки на runner, не запуск viewer.

SHA256SUMS.txt пересчитывается после installer test и включает все файлы dist,
кроме самого списка сумм. Проверять нужно **внутренние** Setup EXE/Portable ZIP,
а не внешнюю ZIP-обёртку GitHub artifact. Checkpoint имеет собственную SHA256
для packaging-inputs.zip.

## Ожидаемые артефакты — срок хранения 30 дней

- `maksfs-integration-fresh-inputs-<run_id>`: свежий binary checkpoint,
  `packaging-inputs.json`, SHA256SUMS; доступен и при последующей ошибке упаковки.
- `MaksFS-integration-test-Setup-<run_id>`: новый Setup EXE.
- `MaksFS-integration-test-Portable-<run_id>`: новый Portable ZIP.
- `MaksFS-integration-test-verification-<run_id>`: verification.json,
  file-manifest.json, SHA256SUMS.txt и installer-test.txt.
- `maksfs-windows-diagnostics-<run_id>-<attempt>`: журналы, provenance,
  CMakeCache и доступные отчёты даже при ошибке (`always()`).

Setup/Portable публикуются как Actions artifacts только после успешных
проверок упаковки и установки, не как официальный релиз. При сбое checkpoint
не следует выдавать за готовый дистрибутив.

## Выполненные проверки подготовки

- `git diff --check`.
- YAML/структура workflow: manual-only, default=false, единственная разрешённая
  ветка, одна compile-команда, ровно выбранный source SHA, отсутствие скачивания
  старых artifacts, checkpoint раньше staging, read-only permissions.
- Python AST всех трёх packaging scripts.
- Изолированный fixture-тест snapshot: provenance и содержимое ZIP, отказ при
  другом checkout SHA. Тест использовал фиктивные данные, не Windows binaries.
- Негативные проверки package.py для старого source SHA, другого run ID,
  другого workflow SHA и fresh_compile=false; проверка отсутствующего
  обязательного EXE и копирования provenance. Все прошли.

PowerShell/NSIS/Windows viewer локально не исполнялись. Полная гарантия
работоспособности workflow появляется только после успешного Actions run.

## Запуск и текущий блокер

Из Cloud GitHub CLI не может обратиться к Actions API: `api.github.com`
отклоняется прокси на CONNECT с HTTP 403 (envoy). Cloud Chromium также не
открывает GitHub: `DNS_PROBE_FINISHED_NO_INTERNET`. GitHub connector предоставляет
чтение jobs/artifacts и rerun, но не dispatch нового workflow. Ограничение
доступа не обходилось. Git transport позволяет сохранить ветку, но это не
предоставляет возможность запустить Actions. Run ID и артефакты до реального
успешного dispatch отсутствуют; результат компиляции пока неизвестен.

Действие владельца, если автоматический dispatch остаётся недоступен:

1. Открыть https://github.com/MaksOnyX26/maksfs-viewer/actions/workflows/maksfs-build-windows.yml
   (в default branch название может отображаться как **MaksFS first Windows build**).
2. Run workflow → **обязательно** выбрать
   `codex/integration-windows-test-20261110`.
3. Включить `confirm_build` и нажать Run workflow **один раз**. Нельзя выбирать
   `maksfs-main`: там находится прежний compile-only workflow.
4. В новом run проверить head branch, workflow commit и identity.txt:
   Source должен быть `07f4f3f7fc83f36fae586de0a21d9c051f2832ab`, а workflow SHA —
   head новой ветки. Сохранить ссылку run и скачать артефакты после успеха.

Альтернатива из авторизованного GitHub CLI владельца:

```sh
gh workflow run maksfs-build-windows.yml --repo MaksOnyX26/maksfs-viewer \
  --ref codex/integration-windows-test-20261110 -f confirm_build=true
gh run list --repo MaksOnyX26/maksfs-viewer --workflow maksfs-build-windows.yml \
  --branch codex/integration-windows-test-20261110 --event workflow_dispatch --limit 1
```

Если GitHub требует approval/Actions write permission, его выполняет владелец.
Для ошибки упаковки использовать сохранённый новый checkpoint в отдельном
packaging-only продолжении с проверкой source SHA; не компилировать повторно
и не брать snapshots из main.

## Оставшиеся проверки

- Успешная компиляция MSVC x64 и создание/проверка обоих пакетов в Actions.
- Установка/удаление и запуск Portable на Windows 11 x64, GPU/драйверы,
  отсутствие missing DLL, работа CEF/VLC/voice/audio.
- Second Life: login, сцена/текстуры, reflections, snapshots, завершение;
  диагностика off/on без заявления измеренного прироста FPS.
- Часы: SLT/местное время/UTC offset/DST, настройки Apply/Cancel/restart,
  три skins, EN/RU, UI scaling/узкое окно, FPS/media/net stats/mouselook.
- OpenSim не включён профилем и не протестирован. Windows 11 и Second Life
  также не объявляются протестированными до фактической проверки.

Основная ветка, интеграционная исходная ветка и Draft PR #1/#2 не меняются;
merge не выполняется.
