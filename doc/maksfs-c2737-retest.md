# Повторная Windows x64 сборка после ошибки диагностики C2737

Подготовлено 2026-11-11 в Codex Cloud. Windows-сборка не запускалась.

## Исправление и причина

[Draft PR #4](https://github.com/MaksOnyX26/maksfs-viewer/pull/4)
направлен в `codex/integration-windows-retest-20261111`.
Исправление: `aa9cf36c89b67e5a01f96acf74b9108241d2492a`.
Одна строка `indra/newview/llappviewer.cpp:1886`:

```cpp
const F64 diagnostic_work_end = diagnose_frame ? frameTimer.getElapsedTimeF64().value() : 0.0;
```

`LLTimer::getElapsedTimeF64()` возвращает `F64SecondsImplicit`
(`LLUnitImplicit<double, LLUnits::Seconds>`), а не F64. В исходном тернарном
выражении один операнд имел этот тип, второй — double. LLUnitImplicit имеет
как неявный конструктор от double, так и неявное преобразование в double,
поэтому тип результата `?:` неоднозначен. Внешний `const F64` не устраняет эту
неоднозначность. Сообщение MSVC C2737 об отсутствующей инициализации является
симптомом некорректного инициализатора; с реальными типами проекта G++ явно
сообщает о разных типах операндов с преобразованием в обе стороны.

`.value()` извлекает F64 в секундах; обе ветви теперь одного типа. const,
условное чтение таймера только при включённой диагностике и точка измерения
сохраняются. В проекте уже используется аналогичное извлечение `.value()`
в условном выражении (`llimagej2ckdu.cpp`).

Просмотрены LL_DISCORD/TRACY_ENABLE блоки: они закрыты до проблемного участка;
объявление и использование времён не разнесены по условным ветвям компиляции.
Проверены все добавленные const: phases, total в record, diagnose_frame,
diagnostic_work_end, total и displayed при записи кадра. Иные очевидные ошибки
компиляции в затронутом коде диагностики не обнаружены. Других исправлений C++ нет.

## Выполненные проверки и ограничения

- `git diff --check` успешно; исправление в PR — одна замена в одном файле.
- Изолированный G++ C++20 harness, `-Wall -Wextra -Werror`, включает реальные
  `lltimer.h`, `llunits.h`, `llunittype.h`; struct диагностики, объявления и
  запись фаз извлечены из актуального `llappviewer.cpp`.
- Static assertions проверяют фактический return type таймера, две неявные
  конверсии и тип F64 у `.value()`.
- Исправленный код компилируется и выполняется: диагностика on/off, startup,
  render/no-render, суммы фаз и число чтений таймера соответствуют ожиданиям.
- Исходное условное выражение в том же harness воспроизводимо не компилируется:
  `each type can be converted to the other`.
- Logging dependency header в harness изолирован; соответствующий dependent
  static_assert macro предоставлен отдельно. Типы единиц не заменялись
  scalar-stubs. Внешние viewer объекты и показания времени — stubs.
- YAML активных workflow и Python syntax packaging scripts проверены.
  SOURCE_SHA/checkout совпадают, manual-only/confirm/default=false и ограничение
  новой веткой сохранены. Проверено, что workflow отличается от source SHA
  ровно тремя значениями, а scripts упаковки и C++ совпадают с source SHA.

Это не MSVC и не компиляция viewer; точный код ошибки G++ отличается от MSVC.
Ранее успешные этапы совместимости, часов и упаковочных fixture-тестов
не повторялись. Нет runtime/GPU/Windows 11/Second Life/OpenSim тестов.

## Новая ветка сборки и происхождение

Ветка: `codex/integration-windows-retest2-20261111`, создана от предыдущей
тестовой ветки с включением исправления только в новую ветку.
**SOURCE_SHA: `aa9cf36c89b67e5a01f96acf74b9108241d2492a`.**
Этот коммит включает ранее исправленный C2664.

В `.github/workflows/maksfs-build-windows.yml` изменены только:

1. Допущенная ветка: `codex/integration-windows-retest2-20261111`.
2. SOURCE_SHA: полный SHA выше.
3. Первый checkout ref: тот же полный SHA.

Workflow SHA отдельно фиксируется через `github.sha`; packaging controls
после компиляции берутся из этого workflow SHA. Скрипты упаковки не менялись.
Сохранены проверки checkout/source SHA, текущих run ID/workflow SHA и
fresh_compile, свежий checkpoint перед упаковкой, Setup EXE/Portable ZIP,
проверки комплектности/установки, provenance и SHA256. Старые артефакты из
maksfs-main не скачиваются. Артефакты хранятся 30 дней; официальный релиз
не публикуется. Windows runner остаётся windows-2022, не Windows 11.

Триггер только `workflow_dispatch`: обязательное Boolean `confirm_build`,
default=false; job допускается только на новой ветке, при confirm_build=true
и run_attempt==1. Сохранение ветки не запускает сборку. Старый failed run
не следует перезапускать: он не получает новый workflow/source SHA.

Основная и прежние тестовые ветки, PR #1/#2/#3 сохранены. PR #4 остаётся Draft,
merge через GitHub не выполнялся. Брендинг и несвязанный код не менялись.

## Ручной запуск владельцем

1. Открыть [GitHub Actions](https://github.com/MaksOnyX26/maksfs-viewer/actions/workflows/maksfs-build-windows.yml).
   В default branch workflow может называться **MaksFS first Windows build**;
   в новой ветке — **MaksFS integration Windows x64 test**.
2. **Run workflow** → выбрать **codex/integration-windows-retest2-20261111**.
3. Включить **confirm_build** → **Run workflow** один раз.
4. В identity.txt/summary проверить Source:
   `aa9cf36c89b67e5a01f96acf74b9108241d2492a`;
   Workflow должен совпадать с head новой ветки на момент dispatch.

Эквивалент через авторизованный CLI владельца:

```sh
gh workflow run maksfs-build-windows.yml --repo MaksOnyX26/maksfs-viewer \
  --ref codex/integration-windows-retest2-20261111 -f confirm_build=true
```

При успехе скачать свежие Setup/Portable и verification artifacts и сверить
SHA256. При ошибке упаковки сначала использовать сохранённый **новый** binary
checkpoint для packaging-only продолжения. Успешная компиляция и упаковка
не заменяют тестирование приложения на Windows 11 и в Second Life.
