# Event Booking History

REST API для управления площадками и мероприятиями, местами в зале и бронированиями. Backend написан на FastAPI; данные хранятся в PostgreSQL, временная блокировка мест — в Redis. [Репозиторий](https://github.com/El1xirq/event-booking-history)

## Возможности

- Регистрация и вход по email и паролю, access- и refresh-токены.
- Роли `customer`, `organizer` и `admin`.
- Создание и управление площадками и местами.
- Создание мероприятий с ценами для мест типов `standard` и `vip`.
- Просмотр доступности мест: `available`, `held` или `sold`.
- Временная блокировка места в Redis при бронировании. TTL задаётся через `HOLD_TTL_SECONDS`; в примере конфигурации — 15 минут.
- Подтверждение, отмена и просмотр бронирований пользователя.
- Миграции схемы базы данных с Alembic.
- Фоновые задачи Celery и периодическая очистка отозванных refresh-токенов.

## Стек

- Python 3.13, FastAPI, Pydantic
- PostgreSQL 16, SQLAlchemy 2, Alembic
- Redis 7
- Celery
- Docker Compose, pytest, Ruff

## Запуск через Docker Compose

Нужны Docker и Docker Compose.

```bash
git clone https://github.com/El1xirq/event-booking-history.git
cd event-booking-history

cp .env.example .env
```

Перед запуском измени в `.env` `POSTGRES_PASSWORD` и `SECRET_KEY`. Для локального запуска пример настроен на Docker Compose. Для окружения с HTTPS установи `DEBUG=False`, чтобы refresh-cookie выставлялась с флагом `Secure`.

```bash
docker compose up --build
```

При старте контейнер приложения применяет миграции Alembic. Compose запускает API, PostgreSQL, Redis, Celery worker и Celery Beat.

- API: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Проверка доступности приложения: <http://localhost:8000/health/live>
- Проверка подключения к PostgreSQL: <http://localhost:8000/health/ready>

Остановить сервисы, не удаляя данные PostgreSQL:

```bash
docker compose down
```

## Переменные окружения

Все перечисленные настройки обязательны для приложения. Полный шаблон находится в `.env.example`.

| Переменная | Назначение |
|---|---|
| `DATABASE_URL` | URL асинхронного подключения к PostgreSQL |
| `SYNC_DATABASE_URL` | URL синхронного подключения; используется, в частности, Alembic и задачами |
| `TEST_DATABASE_URL` | Отдельная база данных для тестов |
| `REDIS_URL` | Redis для приложения и Celery |
| `REDIS_TEST_URL` | Отдельная Redis DB для тестов |
| `POSTGRES_USER` | Пользователь PostgreSQL в Docker Compose |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL |
| `POSTGRES_DB` | Имя основной базы PostgreSQL |
| `HOLD_TTL_SECONDS` | Время временной блокировки места в секундах |
| `SECRET_KEY` | Ключ подписи JWT |
| `ALGORITHM` | Алгоритм подписи JWT, в примере `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Срок действия access-токена |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Срок действия refresh-токена |
| `DEBUG` | Режим отладки; влияет на флаг `Secure` у refresh-cookie |

Не используй значения-заглушки из `.env.example` в production. Храни реальные секреты только в переменных окружения.

## API

Защищённые маршруты принимают access-токен в заголовке:

```http
Authorization: Bearer <access_token>
```

| Метод и путь | Доступ | Описание |
|---|---|---|
| `POST /auth/register` | Без токена | Регистрация пользователя; новая учётная запись получает роль `customer` |
| `POST /auth/login` | Без токена | Вход; refresh-токен устанавливается в HttpOnly-cookie |
| `POST /auth/refresh` | Refresh-cookie | Обновление пары токенов |
| `POST /auth/logout` | Refresh-cookie | Отзыв refresh-токена |
| `GET /auth/me` | Access-токен | Информация о текущем пользователе |
| `GET /venues`, `GET /venues/{venue_id}` | Публичные | Список площадок и информация о площадке |
| `POST /venues` | Организатор или администратор | Создание площадки |
| `PATCH /venues/{venue_id}`, `DELETE /venues/{venue_id}` | Владелец площадки или администратор | Изменение или удаление площадки |
| `GET /venues/{venue_id}/seats` | Публичный | Список мест площадки |
| `POST /venues/{venue_id}/seats` | Владелец площадки или администратор | Добавление места |
| `GET /venues/{venue_id}/seats/{seat_id}` | Публичный | Информация о месте |
| `PATCH /venues/{venue_id}/seats/{seat_id}`, `DELETE /venues/{venue_id}/seats/{seat_id}` | Владелец площадки или администратор | Изменение или удаление места |
| `GET /events`, `GET /events/{event_id}` | Публичные | Список мероприятий и информация о мероприятии |
| `POST /events` | Организатор площадки или администратор | Создание мероприятия |
| `PATCH /events/{event_id}`, `DELETE /events/{event_id}` | Организатор мероприятия или администратор | Изменение или удаление мероприятия |
| `GET /events/{event_id}/seats` | Публичный | Места мероприятия с текущим статусом |
| `POST /reservations` | Клиент или администратор | Временная блокировка места |
| `GET /reservations` | Клиент или администратор | Список бронирований текущего пользователя |
| `GET /reservations/{reservation_id}` | Владелец бронирования или администратор | Просмотр бронирования |
| `PATCH /reservations/{reservation_id}/confirm` | Клиент или администратор | Подтверждение бронирования |
| `DELETE /reservations/{reservation_id}` | Клиент или администратор | Отмена бронирования |

Для списков мероприятий и площадок доступны `skip` и `limit`, например `GET /events?skip=0&limit=20`. Swagger UI на `/docs` показывает схемы запросов и ответов.

## Тесты

Тесты используют отдельные PostgreSQL- и Redis-базы. **Тестовые фикстуры удаляют и пересоздают таблицы в `TEST_DATABASE_URL`, а также очищают базу из `REDIS_TEST_URL`. Не указывай здесь рабочие или важные данные.**

При запуске сервисов через Docker Compose сначала создай тестовую БД:

```bash
docker compose up -d db redis
docker compose exec db psql -U postgres -d event_booking_db \
  -c "CREATE DATABASE event_booking_db_test;"
```

Затем установи зависимости и запусти тесты:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
```

Проверки форматирования и линтинга:

```bash
ruff check .
ruff format --check .
```

## Известные ограничения

- Регистрация создаёт пользователя с ролью `customer`; API для назначения ролей нет.
- Задача подтверждения бронирования пока только записывает сообщение в лог — реальной отправки email нет.
- Платёжная интеграция в проекте не реализована.