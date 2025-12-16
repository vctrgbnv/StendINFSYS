# Stend INFSYS

Учебный проект на Django для хранения метаданных в PostgreSQL и показаний во временных рядах InfluxDB v2. Веб-интерфейс (Bootstrap + Chart.js), REST API (DRF), импорт CSV с Raspberry Pi, OpenAPI спецификация.

## Требования
- Python 3.11+ (локальный запуск)  
- Docker + Docker Compose (поднимает PostgreSQL и InfluxDB)

## Установка и запуск
1. Установите зависимости:
   ```bash
   python3 -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Скопируйте пример окружения:
   ```bash
   cp .env.example .env
   ```
   При необходимости измените пароли/порты. По умолчанию:
   - PostgreSQL: `telemetry/telemetrypass` БД `telemetrydb`
   - InfluxDB v2: `telemetry/telemetrypass`, org `telemetry-org`, bucket `telemetry-bucket`, token `telemetry-token`
3. Поднимите базы:
   ```bash
   docker compose up -d
   ```
4. Примените миграции и создайте суперпользователя:
   ```bash
   .venv/bin/python manage.py migrate
   .venv/bin/python manage.py createsuperuser
   ```
5. Запустите сервер:
   ```bash
   .venv/bin/python manage.py runserver
   ```

## Веб-интерфейс
- Списки и CRUD: `/motor-groups/`, `/sensors/`, `/sessions/`
- Страница сессии с графиками: `/sessions/<id>/`
- Админка: `/admin/`

## Импорт CSV
Формат столбцов (широкий): `ts, throttle, temperature, humidity, rpm, noise, thrust` (`ts` — ISO 8601 или `YYYY-mm-dd HH:MM:SS`). Пример: `sample_data/sample.csv`.

- Через CLI:
  ```bash
  .venv/bin/python manage.py import_csv --session <ID_сессии> sample_data/sample.csv
  ```
- Через API (multipart):
  `POST /api/sessions/<id>/import-csv/` с полем `file`.

Данные пишутся в InfluxDB (measurement `readings`), факт импорта фиксируется в модели `CsvImport`.

## API
- CRUD: `/api/motor-groups/`, `/api/sessions/`, `/api/sensors/`, `/api/sensor-channels/`, `/api/quantities/`
- Серии по величине: `GET /api/sessions/<id>/series/?quantity=temperature&from=...&to=...`
- Импорт CSV: `POST /api/sessions/<id>/import-csv/`
- OpenAPI: `/api/openapi.yaml` (файл в репозитории `openapi.yaml`)

Аутентификация — стандартный Django (session cookie), используйте созданного суперпользователя.

## Полезные заметки
- Бэкенд держит метаданные в PostgreSQL, сами показания живут только в InfluxDB.
- При отсутствии датчиков/каналов для нужной величины при импорте создаётся дефолтный датчик и канал.
- Настройки InfluxDB/БД читаются из `.env` в `stendinfsys/settings.py`.
