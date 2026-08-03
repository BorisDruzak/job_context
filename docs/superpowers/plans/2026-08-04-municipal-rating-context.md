# План реализации репозитория муниципальных рейтингов

> **Для агентных исполнителей:** ОБЯЗАТЕЛЬНЫЙ ПОДНАВЫК: использовать `superpowers:subagent-driven-development` (рекомендуется) либо `superpowers:executing-plans`, выполняя задачи последовательно. Шаги размечены флажками `- [ ]`.

**Цель:** превратить `BorisDruzak/job_context` в проверяемый публичный источник контекста по методикам цифровой трансформации, рейтингам апреля–июня 2026 года, текущему положению Сосновского муниципального округа и применимым поручениям подкомиссии.

**Архитектура:** официальные числовые данные хранятся в CSV/YAML, пояснения и аналитика — в Markdown. Расчётный модуль читает веса методики, исключает неприменимые показатели, перераспределяет их вес и сверяет результат с официальной оценкой. Валидатор проверяет структуру данных, идентификаторы источников и отсутствие персональных контактов в публичных файлах.

**Технологии:** Markdown, CSV, YAML 1.2, Python 3.11+, PyYAML 6.0.2, pytest 8.x, стандартная библиотека Python.

## Глобальные ограничения

- Репозиторий публичный: исходные служебные PDF, телефоны, адреса электронной почты, персональные данные и реквизиты доступа не публикуются.
- Кодировка всех текстовых файлов — UTF-8 без BOM.
- CSV использует запятую как разделитель полей и точку как десятичный разделитель.
- Неизвестное или неприменимое значение хранится как пустое поле CSV либо `null` в YAML; оно не заменяется нулём.
- Каждое официальное числовое значение содержит `source_id` либо находится в строке CSV с колонкой `source_id`.
- Пояснения пользователя помечаются `operator_note`; выводы модели — `inference`.
- Официальные значения не исправляются молча. Расхождение между рассчитанным и опубликованным итогом фиксируется отдельно.
- В методиках 2025 и 2026 годов сохраняется примечание о редакционной коллизии общего суммирования: расчёт использует все объявленные веса, а не визуально указанный верхний предел `6`.

---

## Карта создаваемых файлов

- `README.md` — входная точка и краткий статус Сосновского МО.
- `AGENTS.md` — правила чтения и обновления репозитория в будущих чатах.
- `requirements-dev.txt` — фиксированные зависимости проверки.
- `docs/municipal-work-context.md` — границы муниципальной функции и фактическая роль отдела.
- `docs/methodology/*.md` — человекочитаемое изложение методик и изменений.
- `docs/indicators/*.md` — отдельный паспорт каждого показателя.
- `docs/assignments/subcommission-34-2026-08-03.md` — обезличенный реестр применимых поручений.
- `data/methodology/*.yaml` — машиночитаемые веса, формулы, пороги и подпоказатели.
- `data/ratings/*.csv` — полные официальные сводные таблицы и история Сосновского МО.
- `data/sosnovsky/*.yaml` — текущий статус, детализация, ответственность и поручения.
- `data/sources/manifest.yaml` — реестр исходных документов без публикации самих PDF.
- `reports/sosnovsky-2026-06.md` — официальный срез и отделённая от него аналитика.
- `scripts/calculate_rating.py` — расчёт и сверка рейтинга.
- `scripts/validate_data.py` — контрактная и privacy-проверка данных.
- `tests/*.py` — воспроизводимость расчётов и качество публичного набора.

---

### Задача 1. Базовый контракт репозитория и реестр источников

**Файлы:**
- Создать: `README.md`
- Создать: `AGENTS.md`
- Создать: `.gitignore`
- Создать: `requirements-dev.txt`
- Создать: `data/sources/manifest.yaml`
- Создать: `docs/municipal-work-context.md`
- Тест: `tests/test_data_contracts.py`

**Интерфейсы:**
- Потребляет: утверждённую спецификацию `docs/superpowers/specs/2026-08-04-municipal-rating-context-design.md`.
- Производит: устойчивые `source_id`, на которые будут ссылаться все следующие задачи.

- [ ] **Шаг 1. Создать падающий тест реестра источников**

```python
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_source_manifest_has_unique_required_ids() -> None:
    data = yaml.safe_load((ROOT / "data/sources/manifest.yaml").read_text(encoding="utf-8"))
    sources = data["sources"]
    ids = [item["id"] for item in sources]
    assert len(ids) == len(set(ids))
    assert {
        "methodology-2025-order-147",
        "methodology-2026-order-61",
        "rating-2026-04",
        "rating-2026-05",
        "rating-2026-06",
        "subcommission-34-2026-08-03",
        "operator-context-2026-08-04",
    } <= set(ids)
```

- [ ] **Шаг 2. Запустить тест и подтвердить ожидаемое падение**

Команда: `python -m pytest tests/test_data_contracts.py::test_source_manifest_has_unique_required_ids -q`

Ожидаемый результат: `FileNotFoundError` для `data/sources/manifest.yaml`.

- [ ] **Шаг 3. Создать реестр источников**

Каждая запись должна иметь поля:

```yaml
- id: rating-2026-06
  kind: official_rating_export
  title: "Рейтинг муниципальных образований по показателям цифровой трансформации, июнь 2026"
  effective_period: "2026-06"
  source_file_name: "ОМ-048_июнь_2026_Итоги.pdf"
  repository_copy: false
  contains_personal_contacts: false
  extraction_scope: "сводная таблица и детализация показателей"
  verification_status: verified_against_uploaded_pdf
```

Для презентации указать `contains_personal_contacts: true` и `repository_copy: false`. Для операторского контекста указать `kind: operator_note`, дату и отсутствие внешнего документа.

- [ ] **Шаг 4. Создать README, AGENTS и муниципальный контекст**

`README.md` должен сообщать: назначение репозитория, текущую дату среза, последнюю официальную оценку `79.80%`, место `29`, ссылки на методику, отчёт и данные. `AGENTS.md` должен требовать сначала читать `README.md`, затем действующую методику, `data/sosnovsky/current-status.yaml`, историю и поручения. `docs/municipal-work-context.md` фиксирует 114 внутренних пользователей, двух сотрудников отдела, сопровождение удалённых учреждений, Directum и удалённого подключения, а также роль координатора по поручениям вне прямых полномочий.

- [ ] **Шаг 5. Запустить тест**

Команда: `python -m pytest tests/test_data_contracts.py::test_source_manifest_has_unique_required_ids -q`

Ожидаемый результат: `1 passed`.

- [ ] **Шаг 6. Зафиксировать изменения**

```bash
git add README.md AGENTS.md .gitignore requirements-dev.txt data/sources/manifest.yaml docs/municipal-work-context.md tests/test_data_contracts.py
git commit -m "docs: establish municipal context data contract"
```

---

### Задача 2. Машиночитаемые методики 2025 и 2026 годов

**Файлы:**
- Создать: `data/methodology/indicators-2025.yaml`
- Создать: `data/methodology/indicators-2026.yaml`
- Создать: `docs/methodology/2025.md`
- Создать: `docs/methodology/2026.md`
- Создать: `docs/methodology/changes-2025-to-2026.md`
- Изменить: `tests/test_data_contracts.py`

**Интерфейсы:**
- Потребляет: `source_id` методик из `data/sources/manifest.yaml`.
- Производит: `methodology.indicators[*].code`, `base_weight`, `applicability`, `thresholds` для расчётного модуля.

- [ ] **Шаг 1. Добавить падающие тесты структуры методик**

```python
import pytest


@pytest.mark.parametrize(
    ("path", "expected_count", "expected_weight"),
    [
        ("data/methodology/indicators-2025.yaml", 10, 0.1),
        ("data/methodology/indicators-2026.yaml", 14, 1 / 14),
    ],
)
def test_methodology_indicator_contract(path: str, expected_count: int, expected_weight: float) -> None:
    data = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
    indicators = data["indicators"]
    assert len(indicators) == expected_count
    assert len({item["code"] for item in indicators}) == expected_count
    assert all(abs(float(item["base_weight"]) - expected_weight) < 1e-9 for item in indicators)
    assert abs(sum(float(item["base_weight"]) for item in indicators) - 1.0) < 1e-9
```

- [ ] **Шаг 2. Запустить тест и подтвердить падение из-за отсутствующих YAML**

Команда: `python -m pytest tests/test_data_contracts.py::test_methodology_indicator_contract -q`

- [ ] **Шаг 3. Заполнить методику 2025 года**

Корневые поля:

```yaml
schema_version: 1
methodology_id: methodology-2025
source_id: methodology-2025-order-147
effective_from: "2025-11-07"
indicator_count: 10
overall_groups:
  leader: {minimum: 85.0, maximum: 100.0}
  intermediate: {minimum: 70.0, maximum_exclusive: 85.0}
  lagging: {maximum_exclusive: 70.0}
weight_redistribution: proportional_among_applicable
source_formula_collision: "В формуле указан верхний предел 6, при этом объявлено 10 весов; расчёт использует все 10 показателей."
```

Внести показатели `mszu`, `pos`, `gov_publics`, `goskey`, `transport`, `urban_environment`, `gisogd`, `education`, `sport`, `stray_animals`. Для ПОС сохранить 15 подпоказателей версии 2025. Для каждого показателя указать официальное наименование, формулу в текстовом виде, пороги и источник данных.

- [ ] **Шаг 4. Заполнить методику 2026 года**

Использовать те же корневые поля, `effective_from: "2026-05-27"`, 14 равных весов и показатели 1–14. Указать:

- ветеринария рассчитывается ежеквартально с июня 2026 года за второй квартал;
- образование, спорт и ШПД — ежеквартально;
- показатели 12–14 начинают учитываться с сентября 2026 года за третий квартал;
- ПОС содержит 12 подпоказателей;
- общий рейтинг: лидер от 85%, промежуточная группа от 70% до 84,9%, отстающая ниже 70%.

- [ ] **Шаг 5. Написать человекочитаемые документы**

`2025.md` и `2026.md` должны сохранять официальную нумерацию, формулы, пороги и периодичность. `changes-2025-to-2026.md` должен явно перечислить: добавление ШПД и трёх ИИ-показателей; изменение ПОС с 15 до 12 подпоказателей; ужесточение срока ответов ПОС; изменение шкалы участия в опросах; изменения транспорта и городской среды; даты ввода квартальных показателей.

- [ ] **Шаг 6. Запустить тесты методик**

Команда: `python -m pytest tests/test_data_contracts.py::test_methodology_indicator_contract -q`

Ожидаемый результат: `2 passed`.

- [ ] **Шаг 7. Зафиксировать изменения**

```bash
git add data/methodology docs/methodology tests/test_data_contracts.py
git commit -m "docs: encode 2025 and 2026 rating methodologies"
```

---

### Задача 3. Паспорта 14 показателей и карта ответственности Сосновского МО

**Файлы:**
- Создать: `docs/indicators/01-mszu.md` … `docs/indicators/14-local-ai.md`
- Создать: `data/sosnovsky/indicator-responsibility.yaml`
- Изменить: `tests/test_data_contracts.py`

**Интерфейсы:**
- Потребляет: коды показателей из `indicators-2026.yaml`.
- Производит: фактическую роль отдела, контролируемость и открытые вопросы для отчёта.

- [ ] **Шаг 1. Добавить падающий тест покрытия всех показателей**

```python
def test_responsibility_covers_every_2026_indicator() -> None:
    methodology = yaml.safe_load((ROOT / "data/methodology/indicators-2026.yaml").read_text(encoding="utf-8"))
    responsibility = yaml.safe_load((ROOT / "data/sosnovsky/indicator-responsibility.yaml").read_text(encoding="utf-8"))
    expected = {item["code"] for item in methodology["indicators"]}
    actual = {item["indicator_code"] for item in responsibility["indicators"]}
    assert actual == expected
```

- [ ] **Шаг 2. Запустить тест и подтвердить падение**

Команда: `python -m pytest tests/test_data_contracts.py::test_responsibility_covers_every_2026_indicator -q`

- [ ] **Шаг 3. Создать карту ответственности**

Для каждой записи использовать поля:

```yaml
- indicator_code: pos
  official_owner: null
  department_actual_roles: [coordinator, technical_support]
  controllability: partial
  operator_note: "Отдел участвует в рейтинге ПОС, но процесс и границы ответственности пока не определены; известны задачи по виджетам, опросам и оформлению."
  open_questions:
    - "Какой подразделение является владельцем каждого из 12 подпоказателей ПОС?"
```

Зафиксировать пользовательский контекст без расширительного толкования:

- МСЗУ — данные об электронных и общих обращениях; ситуация стабильная; автоматизация последней очереди.
- ПОС — частичное влияние отдела, процесс не определён; известны виджеты, опросы и ответы.
- Госпаблики — региональный автопостинг, локальная нормализация групп и оформления; результат пока нестабилен.
- Госключ — выполняет другая организация.
- Транспорт — для Сосновского рейтинга фактически отражён как 100%, но пользователь считает его не своей зоной; роль отдела не назначать владельцем.
- Городская среда — основной проблемный показатель; собственники, УК, профильный блок ЖКХ и жители находятся вне прямого подчинения отдела; отдел — координатор.
- ГИСОГД — показатель работает, предметный владелец не отдел ИТ.
- Образование — выполняет другая организация.
- Спорт — отдел показатель не ведёт; официальная применимость требует уточнения, поскольку в сводной строке Сосновского МО значение отсутствует.
- Отлов животных — новый показатель, требуется организовать отработку и контроль данных.
- ШПД — полностью отработан отделом; фактическая роль `owner` и `technical_support`.
- Показатели 12–14 — стартуют с третьего квартала; владелец и план исполнения не определены.

- [ ] **Шаг 4. Создать 14 паспортов показателей**

Каждый файл содержит разделы: официальное определение; формула; пороги; источник; периодичность; значение для Сосновского МО; фактический процесс; роль отдела; автоматизация; открытые вопросы. Ссылаться на YAML методики вместо дублирования неструктурированных чисел без `source_id`.

- [ ] **Шаг 5. Запустить тест покрытия**

Команда: `python -m pytest tests/test_data_contracts.py::test_responsibility_covers_every_2026_indicator -q`

Ожидаемый результат: `1 passed`.

- [ ] **Шаг 6. Зафиксировать изменения**

```bash
git add docs/indicators data/sosnovsky/indicator-responsibility.yaml tests/test_data_contracts.py
git commit -m "docs: document indicators and Sosnovsky responsibilities"
```

---

### Задача 4. Полные рейтинги апреля, мая и июня 2026 года

**Файлы:**
- Создать: `data/ratings/2026-04-overall.csv`
- Создать: `data/ratings/2026-05-overall.csv`
- Создать: `data/ratings/2026-06-overall.csv`
- Изменить: `tests/test_data_contracts.py`

**Интерфейсы:**
- Потребляет: официальные сводные таблицы трёх PDF.
- Производит: по 43 строки на период, используемые историей и сверкой рейтинга.

- [ ] **Шаг 1. Добавить тест количества строк и уникальности мест**

```python
import csv


def read_csv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.parametrize("period", ["2026-04", "2026-05", "2026-06"])
def test_overall_rating_has_43_unique_municipalities(period: str) -> None:
    rows = read_csv(f"data/ratings/{period}-overall.csv")
    assert len(rows) == 43
    assert len({row["municipality"] for row in rows}) == 43
    assert sorted(int(row["rank"]) for row in rows) == list(range(1, 44))
    assert {row["period"] for row in rows} == {period}
```

- [ ] **Шаг 2. Запустить тест и подтвердить падение**

Команда: `python -m pytest tests/test_data_contracts.py::test_overall_rating_has_43_unique_municipalities -q`

- [ ] **Шаг 3. Создать единый CSV-контракт**

Колонки во всех трёх файлах:

```text
period,rank,municipality,mszu,pos,gov_publics,goskey,transport,urban_environment,gisogd,education,sport,stray_animals,broadband,official_total,official_group,source_id
```

Знак `-` из исходной таблицы преобразовывать в пустое поле. Значения процентов записывать с точкой. `official_group`: `leader`, `intermediate`, `lagging`.

- [ ] **Шаг 4. Перенести все 43 строки апреля**

Источник — первая страница `Сводный_рейтинг_ОМСУ_апрель_2026.pdf`. Для Сосновского МО строка должна содержать место `30`, значения `92.76,64.29,80.07,100.00,100.00,28.44,83.13,50.00`, пустой спорт, `38.10` по ШПД и итог `70.75`.

- [ ] **Шаг 5. Перенести все 43 строки мая**

Источник — первая страница `ОМ-048_май_2026(1).pdf`. Для Сосновского МО: место `33`, `92.87,64.29,80.13,100.00,100.00,17.81,83.13,50.00`, спорт и ветеринария пустые, ШПД `38.10`, итог `69.59`.

- [ ] **Шаг 6. Перенести все 43 строки июня**

Источник — первая страница `ОМ-048_июнь_2026_Итоги.pdf`. Для Сосновского МО: место `29`, `92.41,64.29,86.97,100.00,100.00,25.46,83.13,100.00`, спорт пустой, ветеринария `45.74`, ШПД `100.00`, итог `79.80`.

- [ ] **Шаг 7. Запустить тесты CSV**

Команда: `python -m pytest tests/test_data_contracts.py::test_overall_rating_has_43_unique_municipalities -q`

Ожидаемый результат: `3 passed`.

- [ ] **Шаг 8. Зафиксировать изменения**

```bash
git add data/ratings/2026-*-overall.csv tests/test_data_contracts.py
git commit -m "data: import April to June 2026 municipal ratings"
```

---

### Задача 5. История и детальная текущая ситуация Сосновского МО

**Файлы:**
- Создать: `data/ratings/sosnovsky-history.csv`
- Создать: `data/sosnovsky/monthly-details.yaml`
- Создать: `data/sosnovsky/current-status.yaml`
- Изменить: `tests/test_data_contracts.py`

**Интерфейсы:**
- Потребляет: три полных CSV и детализацию страниц рейтингов.
- Производит: единый текущий срез для README и отчёта.

- [ ] **Шаг 1. Добавить тест официальной истории**

```python
def test_sosnovsky_history_matches_official_exports() -> None:
    rows = read_csv("data/ratings/sosnovsky-history.csv")
    actual = [(row["period"], int(row["rank"]), float(row["official_total"])) for row in rows]
    assert actual == [
        ("2026-04", 30, 70.75),
        ("2026-05", 33, 69.59),
        ("2026-06", 29, 79.80),
    ]
```

- [ ] **Шаг 2. Запустить тест и подтвердить падение**

Команда: `python -m pytest tests/test_data_contracts.py::test_sosnovsky_history_matches_official_exports -q`

- [ ] **Шаг 3. Создать историю**

`data/ratings/sosnovsky-history.csv` повторяет общий CSV-контракт, содержит только три строки и дополнительные колонки `change_from_previous` и `source_id`. Изменения: май к апрелю `-1.16`, июнь к маю `10.21`.

- [ ] **Шаг 4. Заполнить детализацию по месяцам**

`monthly-details.yaml` содержит три периода и доступные подпоказатели. Для июня обязательно сохранить:

```yaml
urban_environment:
  total: 25.46
  gosuslugi_dom_users: 8.05
  electronic_general_meetings: 39.13
  max_chats_40_plus: 29.20
pos:
  total: 64.29
  awarded_points: 225
  maximum_points: 350
  weak_subindicators:
    public_participation: 0
    public_hearings: 0
gov_publics:
  total: 86.97
  groups_total: 64
  groups_meeting_posting_norm: 49
  posting_norm_percent: 76.56
  minimum_requirements_factor: 1.0
  engagement_target_achievement: 97.37
mszu:
  total: 92.41
  electronic_requests: 11060
  all_requests: 11969
```

Для апреля и мая сохранить доступные данные МСЗУ, ПОС и госпабликов из соответствующих выгрузок. Не выводить отсутствующие подпоказатели из динамики методом догадки.

- [ ] **Шаг 5. Создать текущий статус**

`current-status.yaml` указывает `as_of: "2026-06-30"`, место `29`, итог `79.80`, группу `intermediate`, изменение `10.21`, сильные показатели и риски. Приоритеты: городская среда, ПОС, ветеринария, подготовка к показателям 12–14. Отдельно указать, что июньский рост в значительной степени связан с квартальным обновлением образования, ветеринарии и ШПД; это аналитический вывод `inference`, а не официальный комментарий источника.

- [ ] **Шаг 6. Запустить тест истории**

Команда: `python -m pytest tests/test_data_contracts.py::test_sosnovsky_history_matches_official_exports -q`

Ожидаемый результат: `1 passed`.

- [ ] **Шаг 7. Зафиксировать изменения**

```bash
git add data/ratings/sosnovsky-history.csv data/sosnovsky/monthly-details.yaml data/sosnovsky/current-status.yaml tests/test_data_contracts.py
git commit -m "data: add Sosnovsky rating history and current status"
```

---

### Задача 6. Поручения XXXIV подкомиссии

**Файлы:**
- Создать: `data/sosnovsky/assignments.yaml`
- Создать: `docs/assignments/subcommission-34-2026-08-03.md`
- Изменить: `tests/test_data_contracts.py`

**Интерфейсы:**
- Потребляет: презентацию XXXIV заседания и операторское пояснение о координаторской роли.
- Производит: обезличенный реестр поручений с применимостью, сроком и владельцем.

- [ ] **Шаг 1. Добавить тест уникальности поручений и отсутствия контактов**

```python
import re


def test_assignments_are_unique_and_contact_free() -> None:
    data = yaml.safe_load((ROOT / "data/sosnovsky/assignments.yaml").read_text(encoding="utf-8"))
    ids = [item["id"] for item in data["assignments"]]
    assert len(ids) == len(set(ids))
    text = (ROOT / "docs/assignments/subcommission-34-2026-08-03.md").read_text(encoding="utf-8")
    assert not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-zА-Яа-я]{2,}", text)
    assert not re.search(r"(?:\+7|8)\s*\(?\d{3}\)?[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}", text)
```

- [ ] **Шаг 2. Запустить тест и подтвердить падение**

Команда: `python -m pytest tests/test_data_contracts.py::test_assignments_are_unique_and_contact_free -q`

- [ ] **Шаг 3. Извлечь все поручения, где прямо указан Сосновский МО либо все муниципальные образования**

Минимально включить:

- возможность льгот по земельному налогу организациям почтовой связи, срок 01.09.2026;
- ежеквартальное достижение ШПД 100% и заполнение ОМ-100 до 15 числа последнего месяца квартала;
- онлайн-собрания собственников через ГИС ЖКХ не менее 60%, постоянно;
- перевод домовых чатов в MAX и достижение 40+ участников, постоянно;
- постоянные пользователи «Госуслуги.Дом» не менее 35%, постоянно;
- подготовку личных кабинетов управляющих компаний к работе в ПОС;
- общие для всех муниципалитетов поручения по ГИС РСУД, данным, ИИ, ПОС и иным направлениям, обнаруженные при полном просмотре презентации.

Не включать фамилии, телефоны и электронную почту. Для каждого пункта сохранить номер слайда/пункта, срок, статус, предметного владельца и роль отдела. Поручения ЖКХ маркировать как `department_role: coordinator`, а не как полномочие непосредственного исполнения.

- [ ] **Шаг 4. Написать Markdown-отчёт по поручениям**

Сгруппировать на: постоянный контроль; разовые сроки; поручения вне прямых полномочий; открытые вопросы. Указать, что презентация отражает оперативную интерпретацию, но не заменяет протокол.

- [ ] **Шаг 5. Запустить тест**

Команда: `python -m pytest tests/test_data_contracts.py::test_assignments_are_unique_and_contact_free -q`

Ожидаемый результат: `1 passed`.

- [ ] **Шаг 6. Зафиксировать изменения**

```bash
git add data/sosnovsky/assignments.yaml docs/assignments/subcommission-34-2026-08-03.md tests/test_data_contracts.py
git commit -m "docs: register Sosnovsky subcommission assignments"
```

---

### Задача 7. Расчёт рейтинга и автоматическая сверка

**Файлы:**
- Создать: `scripts/calculate_rating.py`
- Создать: `tests/test_calculate_rating.py`

**Интерфейсы:**
- Потребляет: словарь значений `dict[str, float | None]` и веса из YAML.
- Производит:
  - `redistribute_weights(weights, values) -> dict[str, float]`
  - `calculate_score(weights, values) -> float`
  - `classify_score(score) -> str`
  - `compare_with_official(calculated, official, tolerance=0.02) -> dict[str, float | bool]`

- [ ] **Шаг 1. Написать падающие модульные тесты**

```python
from scripts.calculate_rating import (
    calculate_score,
    classify_score,
    compare_with_official,
    redistribute_weights,
)


def test_redistributes_missing_equal_weight_indicator() -> None:
    weights = {"a": 0.25, "b": 0.25, "c": 0.25, "d": 0.25}
    values = {"a": 100.0, "b": 50.0, "c": None, "d": 0.0}
    actual = redistribute_weights(weights, values)
    assert actual == {"a": 1 / 3, "b": 1 / 3, "d": 1 / 3}
    assert calculate_score(weights, values) == 50.0


def test_classifies_official_groups() -> None:
    assert classify_score(85.0) == "leader"
    assert classify_score(70.0) == "intermediate"
    assert classify_score(69.999) == "lagging"


def test_compare_uses_rounding_tolerance() -> None:
    result = compare_with_official(79.795, 79.80)
    assert result["matches"] is True
```

- [ ] **Шаг 2. Запустить тесты и подтвердить падение импорта**

Команда: `python -m pytest tests/test_calculate_rating.py -q`

- [ ] **Шаг 3. Реализовать минимальный расчётный модуль**

```python
from __future__ import annotations


def redistribute_weights(
    weights: dict[str, float], values: dict[str, float | None]
) -> dict[str, float]:
    applicable = {code: weight for code, weight in weights.items() if values.get(code) is not None}
    total = sum(applicable.values())
    if total <= 0:
        raise ValueError("at least one indicator must be applicable")
    return {code: weight / total for code, weight in applicable.items()}


def calculate_score(weights: dict[str, float], values: dict[str, float | None]) -> float:
    effective = redistribute_weights(weights, values)
    return sum(float(values[code]) * weight for code, weight in effective.items())


def classify_score(score: float) -> str:
    if score >= 85.0:
        return "leader"
    if score >= 70.0:
        return "intermediate"
    return "lagging"


def compare_with_official(
    calculated: float, official: float, tolerance: float = 0.02
) -> dict[str, float | bool]:
    delta = calculated - official
    return {
        "calculated": calculated,
        "official": official,
        "delta": delta,
        "matches": abs(delta) <= tolerance,
    }
```

- [ ] **Шаг 4. Добавить параметризованную сверку Сосновского МО**

Тест читает строки из трёх полных CSV, формирует значения только непустых показателей и проверяет соответствие официальному итогу с допуском `0.02`. Если апрельская или майская выгрузка применяла переходный набор показателей, веса брать из фактически представленных колонок с равным перераспределением и документировать расхождение, а не подгонять данные.

- [ ] **Шаг 5. Запустить расчётные тесты**

Команда: `python -m pytest tests/test_calculate_rating.py -q`

Ожидаемый результат: все тесты проходят либо известное официальное расхождение оформлено как явный `xfail` с точным объяснением источника.

- [ ] **Шаг 6. Зафиксировать изменения**

```bash
git add scripts/calculate_rating.py tests/test_calculate_rating.py
git commit -m "feat: add municipal rating calculator"
```

---

### Задача 8. Валидатор публичного набора

**Файлы:**
- Создать: `scripts/validate_data.py`
- Изменить: `tests/test_data_contracts.py`

**Интерфейсы:**
- Потребляет: корень репозитория.
- Производит: код возврата `0` при валидном наборе и ненулевой код с перечнем нарушений.

- [ ] **Шаг 1. Добавить падающий тест privacy-сканера**

```python
from scripts.validate_data import scan_public_text


def test_public_text_scanner_detects_contacts() -> None:
    findings = scan_public_text("Позвонить +7 (351) 111-22-33 или user@example.org")
    assert {item["kind"] for item in findings} == {"email", "phone"}


def test_repository_public_files_have_no_contacts() -> None:
    from scripts.validate_data import validate_repository

    assert validate_repository(ROOT) == []
```

- [ ] **Шаг 2. Запустить тесты и подтвердить падение импорта**

Команда: `python -m pytest tests/test_data_contracts.py -q`

- [ ] **Шаг 3. Реализовать сканер и структурные проверки**

`scan_public_text()` использует регулярные выражения для электронной почты, российских телефонных номеров и типичных секретов (`password=`, `token=`, `api_key=`). `validate_repository()` проверяет Markdown/YAML/CSV, исключая `.git`, и дополнительно проверяет обязательные поля источников, уникальность идентификаторов, 43 строки полных рейтингов и существование каждого документа показателя.

- [ ] **Шаг 4. Добавить CLI**

```python
if __name__ == "__main__":
    from pathlib import Path

    errors = validate_repository(Path(__file__).resolve().parents[1])
    for error in errors:
        print(error)
    raise SystemExit(1 if errors else 0)
```

- [ ] **Шаг 5. Запустить полный валидатор**

Команда: `python scripts/validate_data.py`

Ожидаемый результат: код `0`, вывода ошибок нет.

- [ ] **Шаг 6. Зафиксировать изменения**

```bash
git add scripts/validate_data.py tests/test_data_contracts.py
git commit -m "test: validate public municipal rating dataset"
```

---

### Задача 9. Аналитический отчёт и финальная навигация

**Файлы:**
- Создать: `reports/sosnovsky-2026-06.md`
- Изменить: `README.md`
- Изменить: `AGENTS.md`

**Интерфейсы:**
- Потребляет: `current-status.yaml`, историю, детализацию, ответственность и поручения.
- Производит: компактный управленческий отчёт и стабильный вход для будущих чатов.

- [ ] **Шаг 1. Написать официальный раздел отчёта**

Зафиксировать без интерпретации:

- апрель: `70,75%`, место `30`;
- май: `69,59%`, место `33`;
- июнь: `79,80%`, место `29`;
- динамика июня к маю: `+10,21 п. п.`;
- июньские значения: МСЗУ `92,41%`, ПОС `64,29%`, госпаблики `86,97%`, Госключ `100%`, транспорт `100%`, городская среда `25,46%`, ГИСОГД `83,13%`, образование `100%`, спорт неприменим/отсутствует в строке, ветеринария `45,74%`, ШПД `100%`.

- [ ] **Шаг 2. Написать аналитический раздел**

Отдельно маркировать `inference`:

- главный управляемый резерв — ПОС: 225 из 350 баллов; нулевые баллы по участию граждан и публичным слушаниям;
- главный межведомственный риск — городская среда: `8,05%`, `39,13%`, `29,20%` по трём компонентам;
- госпаблики улучшились на `6,84 п. п.`, но только 49 из 64 групп выполнили норму публикаций;
- МСЗУ стабильно высок, автоматизация не является первой очередью;
- ШПД восстановлен до 100% после 38,10% в апреле–мае;
- ветеринария требует нового процесса контроля заявок;
- показатели 12–14 создают риск третьего квартала и требуют назначения владельцев.

- [ ] **Шаг 3. Добавить матрицу действий**

Для каждого приоритета указать: действие, предметного владельца, роль отдела, измеримый результат, срок следующего контроля и источник данных. Не назначать отдел исполнителем собраний собственников, набора жителей в чаты или профильной работы с животными без подтверждённых полномочий.

- [ ] **Шаг 4. Обновить README и AGENTS**

README должен ссылаться на отчёт, методику 2026, историю, текущий YAML и поручения. AGENTS должен объяснять, что официальный факт, `operator_note` и `inference` нельзя смешивать, а новая выгрузка добавляется исторически без перезаписи прошлых периодов.

- [ ] **Шаг 5. Запустить все проверки**

```bash
python -m pytest -q
python scripts/validate_data.py
```

Ожидаемый результат: все тесты проходят, валидатор возвращает `0`.

- [ ] **Шаг 6. Зафиксировать изменения**

```bash
git add reports/sosnovsky-2026-06.md README.md AGENTS.md
git commit -m "docs: publish Sosnovsky June 2026 rating report"
```

---

### Задача 10. Финальная проверка и публикация

**Файлы:**
- Изменить только файлы, в которых проверки выявили конкретную ошибку.

**Интерфейсы:**
- Потребляет: весь репозиторий.
- Производит: проверенный набор данных в ветке `main`.

- [ ] **Шаг 1. Проверить рабочее дерево**

Команда: `git status --short`

Ожидаемый результат: нет незакоммиченных файлов.

- [ ] **Шаг 2. Выполнить полный набор тестов**

Команда: `python -m pytest -q`

Ожидаемый результат: все тесты проходят без неожиданных `xfail`.

- [ ] **Шаг 3. Запустить публичный валидатор**

Команда: `python scripts/validate_data.py`

Ожидаемый результат: код `0`.

- [ ] **Шаг 4. Выборочно сверить официальные значения**

Проверить строки Сосновского МО во всех трёх CSV, июньскую детализацию ПОС, госпабликов, городской среды, МСЗУ, ветеринарии и ШПД непосредственно с соответствующими страницами PDF. Проверить, что презентационные контакты не попали в Git.

- [ ] **Шаг 5. Проверить историю коммитов**

Команда: `git log --oneline --decorate -12`

Ожидаемый результат: отдельные коммиты по контракту, методикам, показателям, рейтингам, истории, поручениям, расчёту, валидации и отчёту.

- [ ] **Шаг 6. Зафиксировать только необходимые исправления**

```bash
git add <исправленные-файлы>
git commit -m "fix: resolve municipal context verification findings"
```

Этот коммит создаётся только при фактических исправлениях; пустой коммит запрещён.

---

## Самопроверка плана

- Спецификация покрыта: методики, 14 показателей, три полных рейтинга, история Сосновского МО, ответственность, поручения, расчёт, валидация, отчёт и навигация имеют отдельные задачи.
- Незаданных заглушек `TBD`/`TODO` нет.
- Имена функций согласованы между задачами 7 и 8.
- Неизвестные владельцы и отсутствующие официальные значения сохраняются как `null`, а не выдумываются.
- Публичные ограничения и отделение официальных данных от `operator_note`/`inference` проверяются автоматически.
