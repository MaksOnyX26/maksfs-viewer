# MaksFS

Экспериментальный fork Firestorm для Second Life с целью снизить нагрузку на компьютер и улучшить плавность работы. Улучшения производительности пока не реализованы и не измерены. Готовых сборок MaksFS пока нет.

## Основа

- Upstream: https://github.com/FirestormViewer/phoenix-firestorm
- Рабочая ветка: `maksfs-main`; исходная релизная ветка: `Firestorm_7.2.5`.
- Подтверждённый официальный тег: [Firestorm_Release_7.2.5.81788](https://github.com/FirestormViewer/phoenix-firestorm/tree/Firestorm_Release_7.2.5.81788).
- Базовый коммит: `4ac201fdc56127de27de34567286885f4e75d194`.
- Проверено 2026-11-08: upstream-ветка, релизный тег и ветка fork совпадают. Ветка создана от этого коммита, не от master.
- История upstream сохранена. Оригинальный README без изменений: [README.upstream.md](README.upstream.md).

MaksFS — самостоятельный эксперимент, не официальный выпуск Firestorm и не продукт Linden Lab.

## Начало работы

[План](ROADMAP.md) · [Подготовка Windows и ограничения CI](BUILDING.md)

На этом этапе меняются только документация и организация CI. Компиляция, загрузка библиотек, создание установщика и публикация требуют отдельного решения.

## Лицензии и атрибуция

Сохранены [LICENSE](LICENSE), [лицензия исходников](doc/LICENSE-source.txt), [LGPL 2.1](doc/LGPL-license.txt), [правила для логотипов](doc/LICENSE-logos.txt), [заголовок Firestorm](FIRESTORM-SOURCE_LICENSE_HEADER.txt) и авторство исходных файлов. Заголовок Firestorm указывает LGPL **2.1 only**; отдельные файлы и зависимости могут иметь другие условия.

При изменении и распространении нужно сохранять уведомления, отмечать изменения и выполнять применимые требования LGPL к исходникам и возможности перелинковки. Лицензия исходников не заменяет лицензии сторонних SDK и правила использования товарных знаков. Перед выпуском требуется отдельная проверка комплекта библиотек, брендинга и [Second Life Third-Party Viewer Policy](https://secondlife.com/corporate/third-party-viewers).

