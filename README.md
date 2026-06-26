# Real Estate KZ - Астана Market Monitor

Автоматизированная система мониторинга и анализа рынка жилой недвижимости Казахстана.
Фокус: **продажа квартир в Астане** с анализом по всем 6 районам.

## 🎯 Основные возможности

- 🏢 Парсинг данных о продаже квартир с krisha.kz
- 🗺️ Фильтрация по всем 6 районам Астаны (Нура, Есильский, Алматы, Сарыарка, Байконур, Сарайшык)
- 📊 Расчет метрик: средняя цена/м², средняя площадь, количество объектов
- 📈 Сохранение исторических данных для анализа динамики цен
- 🔄 Автоматические периодические запуски (cron)
- 💾 Хранилище: SQLite (легко масштабировать на PostgreSQL)
- 🎯 Анализ инвестиционной привлекательности по ЖК

## 📋 Требования

- Python 3.10+
- requests
- BeautifulSoup4
- pandas
- SQLite3 (встроен в Python)

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/daconna/Real-Estate-Parser.git
cd Real-Estate-Parser
```

### 2. Создание виртуального окружения

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка параметров поиска

Отредактируйте `SEARCH_PARAMETERS.json`:

```json
{
  "city": 2,
  "city_name": "astana",
  "districts": [
    {
      "name": "nura",
      "display_name": "Нура",
      "url_slug": "astana-nura"
    },
    {
      "name": "esilskij",
      "display_name": "Есильский",
      "url_slug": "astana-esilskij"
    },
    {
      "name": "almatinskij",
      "display_name": "Алматы",
      "url_slug": "astana-almatinskij"
    },
    {
      "name": "saryarkinskij",
      "display_name": "Сарыарка",
      "url_slug": "astana-saryarkinskij"
    },
    {
      "name": "bajkonur",
      "display_name": "Байконур",
      "url_slug": "r-n-bajkonur"
    },
    {
      "name": "saraishyk",
      "display_name": "Сарайшык",
      "url_slug": "astana-saraishyk"
    }
  ],
  "search_params": {
    "rooms": [1, 2, 3],
    "price_from": 5000000,
    "price_to": 100000000,
    "has_photo": true,
    "furniture": null,
    "owner": null
  }
}
```

### 5. Запуск парсера

```bash
python -m krisha_parser
```

## ⚙️ Параметры конфигурации

### SEARCH_PARAMETERS.json

#### Основные параметры:
- **city** - код города (2 = Астана)
- **city_name** - название города
- **districts** - массив объектов районов с параметрами:
  - `name` - внутренний идентификатор
  - `display_name` - название для отображения
  - `url_slug` - URL слаг на krisha.kz

#### Параметры поиска:
- **rooms** - количество комнат [1, 2, 3, 4, 5]
- **price_from** - минимальная цена (тенге)
- **price_to** - максимальная цена (тенге)
- **has_photo** - только объявления с фото (true/false)
- **furniture** - мебель (true/false/null)
- **owner** - только от собственников (true/false/null)

### Все 6 районов Астаны

| Район | URL слаг | Код |
|-------|----------|-----|
| Нура | astana-nura | nura |
| Есильский | astana-esilskij | esilskij |
| Алматы | astana-almatinskij | almatinskij |
| Сарыарка | astana-saryarkinskij | saryarkinskij |
| Байконур | r-n-bajkonur | bajkonur |
| Сарайшык | astana-saraishyk | saraishyk |

### Примеры конфигураций

#### Пример 1: Нура, 1-3 комнаты, бюджет 5-50 млн

```json
{
  "city": 2,
  "districts": [{
    "name": "nura",
    "display_name": "Нура",
    "url_slug": "astana-nura"
  }],
  "search_params": {
    "rooms": [1, 2, 3],
    "price_from": 5000000,
    "price_to": 50000000,
    "has_photo": true
  }
}
```

#### Пример 2: Все районы, премиум сегмент

```json
{
  "city": 2,
  "districts": [все 6 районов],
  "search_params": {
    "rooms": [2, 3],
    "price_from": 30000000,
    "price_to": 200000000,
    "has_photo": true,
    "owner": true
  }
}
```

## 📊 Структура БД

### Таблица `apartments`

Хранит все спарсенные объявления о продаже:

```
id (INTEGER PRIMARY KEY)
krisha_id (TEXT UNIQUE) - ID объявления на krisha.kz
jk_name (TEXT) - название ЖК
district (TEXT) - район
address (TEXT) - адрес
price (INTEGER) - цена (тенге)
area (REAL) - площадь (м²)
rooms (INTEGER) - количество комнат
price_per_sqm (REAL) - цена за м²
description (TEXT) - описание
photos_count (INTEGER) - количество фото
phone (TEXT) - телефон продавца
seller_type (TEXT) - тип продавца (owner/agency/realtor)
url (TEXT) - ссылка на объявление krisha.kz
parsed_at (TIMESTAMP) - время парсинга
created_at (TIMESTAMP) - дата создания (первый раз найдено)
updated_at (TIMESTAMP) - дата последнего обновления
```

### Таблица `jk_metrics`

Агрегированные метрики по ЖК (рассчитывается при каждом парсинге):

```
id (INTEGER PRIMARY KEY)
jk_name (TEXT)
district (TEXT)
avg_price (REAL) - средняя цена
avg_price_per_sqm (REAL) - средняя цена за м²
avg_area (REAL) - средняя площадь
median_price (REAL) - медианная цена
count_total (INTEGER) - всего объявлений
count_1room (INTEGER) - 1-комн.
count_2room (INTEGER) - 2-комн.
count_3plus_room (INTEGER) - 3+ комн.
min_price (INTEGER)
max_price (INTEGER)
snapshot_date (DATE) - дата снимка
```

## 🔄 Автоматические запуски (Cron)

Отредактируйте `cron.sh`:

```bash
#!/bin/bash
cd /path/to/Real-Estate-Parser
source .venv/bin/activate
python -m krisha_parser
```

Добавьте в crontab:

```bash
crontab -e
```

```cron
# Запуск каждый день в 12:00
0 12 * * * /path/to/Real-Estate-Parser/cron.sh

# Запуск каждый час
0 * * * * /path/to/Real-Estate-Parser/cron.sh

# Запуск каждые 6 часов
0 */6 * * * /path/to/Real-Estate-Parser/cron.sh
```

## 📈 Анализ данных

Используйте pandas для анализа:

```python
import pandas as pd
import sqlite3

conn = sqlite3.connect('krisha_data.db')

# Последние 100 объявлений
df = pd.read_sql_query(
    "SELECT * FROM apartments ORDER BY parsed_at DESC LIMIT 100",
    conn
)

# Средняя цена по районам
by_district = df.groupby('district')['price_per_sqm'].agg(['mean', 'median', 'count'])
print(by_district)

# Метрики по ЖК
metrics = pd.read_sql_query(
    "SELECT * FROM jk_metrics ORDER BY snapshot_date DESC",
    conn
)
print(metrics)
```

## ⚠️ Важные замечания

- Парсер соблюдает задержку между запросами (~2 сек) для уважения к серверам krisha.kz
- Данные сохраняются с timestamp для отслеживания динамики
- При переполнении очереди парсер автоматически повторяет запрос с экспоненциальной задержкой
- **Использование парсера должно соответствовать Terms of Service krisha.kz**

## 📝 Лицензия

MIT

## 👤 Автор

daconna

## 🤝 Вклад

Если вы хотите добавить функции (поддержку других городов, визуализацию, новые метрики) - пожалуйста, создавайте Pull Requests!

---

**Планы развития:**

- [ ] Полная реализация парсинга HTML (CSS селекторы)
- [ ] Поддержка других городов Казахстана
- [ ] REST API для доступа к данным
- [ ] Web dashboard с картой и графиками
- [ ] PostgreSQL вместо SQLite для масштабирования
- [ ] Уведомления при изменении цен
- [ ] Интеграция с Google Sheets для экспорта
- [ ] Docker контейнер для упрощенного развертывания
- [ ] Анализ инвестиционной привлекательности
