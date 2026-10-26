# Expense Tracker API

Небольшой сервис на FastAPI для учёта личных расходов: можно записывать траты по категориям,
смотреть и фильтровать их, удалять ошибочные записи и получать сводку за месяц с остатком бюджета.

**Для кого:** для человека, который хочет быстро вести учёт трат через HTTP API
(из скрипта, Telegram-бота, Postman или прямо из Swagger UI на `/docs`).

Данные хранятся в памяти процесса и сбрасываются при перезапуске — база данных в учебном проекте не используется.

## Маршруты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Информация о сервисе |
| GET | `/health` | Проверка работоспособности (`status`, `uptime_seconds`) |
| GET | `/version` | Название и версия приложения |
| GET | `/categories` | Список допустимых категорий |
| POST | `/expenses` | Добавить расход (`amount`, `category`, `description`, `spent_on`) |
| GET | `/expenses?category=food` | Список расходов, опционально с фильтром по категории |
| GET | `/expenses/{expense_id}` | Получить расход по id (404, если нет) |
| DELETE | `/expenses/{expense_id}` | Удалить расход |
| GET | `/summary?month=YYYY-MM` | Сумма по категориям за месяц, остаток бюджета и флаг превышения |

Категории: `food`, `transport`, `housing`, `health`, `entertainment`, `other` (регистр не важен).

## Быстрый старт

Нужны Docker и `make`. Одна команда собирает образ и запускает контейнер:

```bash
git clone https://github.com/Screxy/expense-tracker-api.git
cd expense-tracker-api
make up        # сборка образа + запуск на http://127.0.0.1:8000/docs
make health    # проверить /health и /version
make logs      # смотреть логи
make down      # остановить
```

Все команды: `make help`.

| Команда | Что делает |
|---------|------------|
| `make install` | Создаёт `.venv`, ставит зависимости, копирует `.env.example` в `.env` |
| `make run` | Запуск локально без `--reload` |
| `make dev` | Запуск локально с `--reload` |
| `make test` | `python -m pytest -v` |
| `make up` / `make down` | Запуск / остановка в Docker |
| `make logs` | Логи контейнера |
| `make health` | Запросы к `/health` и `/version` |
| `make clean` | Удаляет `.venv`, кэши, контейнер и образ |

Порт можно поменять: `make up PORT=8080`.

## Установка

Нужен Python 3.9+.

```bash
git clone https://github.com/Screxy/expense-tracker-api.git
cd expense-tracker-api

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements-dev.txt   # для работы и тестов
# или только runtime-зависимости:
# pip install -r requirements.txt
```

## Переменные окружения

Все переменные необязательные — есть значения по умолчанию. Пример лежит в `.env.example`:

```bash
cp .env.example .env
```

| Переменная | По умолчанию | Назначение |
|------------|--------------|------------|
| `APP_NAME` | `Expense Tracker API` | Название сервиса в `/version` и `/docs` |
| `APP_VERSION` | `1.0.0` | Версия, которую отдаёт `/version` |
| `LOG_LEVEL` | `INFO` | Уровень логов: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `CURRENCY` | `RUB` | Валюта в сводке и логах |
| `MONTHLY_BUDGET` | `50000` | Месячный бюджет для `/summary` |

Файл `.env` добавлен в `.gitignore` и не публикуется — в репозитории есть только безопасный `.env.example`.

## Запуск

Обычный запуск (без `--reload`):

```bash
uvicorn app_final:app --host 0.0.0.0 --port 8000 --env-file .env
```

Если `.env` не создан, просто уберите `--env-file .env` — будут использованы значения по умолчанию.

Режим разработки с автоперезагрузкой:

```bash
uvicorn app_final:app --reload --env-file .env
```

После запуска откройте документацию: <http://127.0.0.1:8000/docs>

### Запуск в Docker без make

```bash
docker build -t expense-tracker-api .
docker run -d --name expense-tracker -p 8000:8000 --env-file .env expense-tracker-api
docker logs -f expense-tracker
```

Образ основан на `python:3.12-slim`, приложение работает от непривилегированного пользователя,
в образ встроен `HEALTHCHECK` по `/health` (состояние видно в `docker ps`). Файл `.env` в образ
не копируется (`.dockerignore`) — переменные передаются при запуске через `--env-file`.

Пример работы:

```bash
curl -X POST http://127.0.0.1:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{"amount": 350, "category": "food", "description": "Обед"}'

curl http://127.0.0.1:8000/expenses?category=food
curl http://127.0.0.1:8000/summary
```

## Тесты

```bash
python -m pytest -v
```

Тесты в `test_app.py` проверяют `/health`, `/version`, создание/получение/удаление расходов,
фильтрацию, ошибки (404, неизвестная категория, отрицательная сумма, неверный формат месяца)
и расчёт сводки с превышением бюджета.

## CI

Workflow `.github/workflows/ci.yml` запускается на каждый `push` и `pull_request`:

1. ставит зависимости на Python 3.9 и 3.12;
2. запускает `python -m pytest -v`;
3. делает smoke-тест: поднимает приложение через uvicorn и проверяет `/health`;
4. после успешных проверок загружает artifact `expense-tracker-app`
   (`app_final.py`, `requirements.txt`, `README.md`, `.env.example`);
5. отдельный job `docker` собирает образ, запускает контейнер и проверяет `/health`.

Artifact можно скачать на странице запуска во вкладке **Actions → нужный запуск → Artifacts**.

## Диагностика

**Проверка, что сервис жив:**

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok","uptime_seconds":12.3}

curl http://127.0.0.1:8000/version
# {"name":"Expense Tracker API","version":"1.0.0"}
```

**Где смотреть логи.** Приложение пишет логи в стандартный вывод (терминал, в котором запущен uvicorn).
В Docker — `make logs` или `docker logs -f expense-tracker`; состояние healthcheck — `docker ps`
(колонка STATUS: `healthy` / `unhealthy`). Время в логах контейнера — UTC.
Чтобы сохранить их в файл:

```bash
uvicorn app_final:app --env-file .env 2>&1 | tee app.log
```

Что пишется в лог:

- запуск и остановка с текущими настройками:
  `INFO [expense_tracker] Starting Expense Tracker API v1.0.0 (currency=RUB, monthly_budget=50000.00)`
- каждый запрос, код ответа и время:
  `INFO [expense_tracker] GET /health -> 200 (0.6 ms)`
- создание и удаление расходов:
  `INFO [expense_tracker] Created expense #1: 350.00 RUB (food)`
- отклонённые данные и превышение бюджета (уровень `WARNING`):
  `WARNING [expense_tracker] Budget exceeded for 2026-10: 52000.00 > 50000.00 RUB`

Для подробного вывода запустите с `LOG_LEVEL=DEBUG`.

**Типичные проблемы:**

| Симптом | Причина и решение |
|---------|-------------------|
| `ModuleNotFoundError: No module named 'fastapi'` | Не активировано окружение или не установлены зависимости: `source .venv/bin/activate && pip install -r requirements-dev.txt` |
| `Address already in use` | Порт 8000 занят: запустите с `--port 8001` или остановите другой процесс (`lsof -i :8000`) |
| `ValueError: could not convert string to float` при старте | В `MONTHLY_BUDGET` записано не число — исправьте `.env` |
| `422 Unknown category` | Категории нет в списке — посмотрите `GET /categories` |
| `Conflict. The container name "/expense-tracker" is already in use` | Старый контейнер не удалён: `make down`, затем `make up` (`make up` делает это сам) |
| `Cannot connect to the Docker daemon` | Docker не запущен — запустите Docker Desktop |
| Данные пропали | Хранилище в памяти, после перезапуска оно пустое — это ожидаемо |

## Источник

Структура проекта основана на учебном примере `app_final.py` с занятий курса
«Инфраструктура и администрирование». Тема, маршруты, логика учёта расходов, настройки,
логирование и тесты написаны самостоятельно.
