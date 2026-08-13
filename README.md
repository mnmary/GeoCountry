# 🌍 GeoCountry

Полноценное фулстек-приложение для определения страны по географическим координатам.
Backend — **FastAPI** (async, PostgreSQL), frontend — **Vue 3 SPA** на **Pico.css**, взаимодействие через **Axios** и REST API с JWT-аутентификацией.

## Возможности

- Регистрация и авторизация пользователей (email + пароль)
- JWT-аутентификация: короткоживущий access-токен + долгоживущий refresh-токен (хранится в БД, привязан к сессии)
- Автоматическое обновление access-токена по refresh-токену на фронтенде (interceptor Axios)
- Определение страны по широте и долготе через геокодер **Nominatim (OpenStreetMap)**
- Сохранение каждого запроса в историю (координаты, страна, пользователь)
- Ролевая модель: `user` / `admin` — админ видит историю всех пользователей, обычный юзер — только свою
- Автоматическое создание учётной записи администратора при первом запуске (из переменных окружения)
- Выход из системы с инвалидацией refresh-токена

## Архитектура и стек технологий

### Backend

| Компонент         | Технология                                                    |
|--------------------|----------------------------------------------------------------|
| Веб-фреймворк      | [FastAPI](https://fastapi.tiangolo.com/) 0.141                 |
| ORM / БД           | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (async) + [asyncpg](https://github.com/MagicStack/asyncpg) (PostgreSQL) |
| Валидация          | [Pydantic v2](https://docs.pydantic.dev/)                      |
| Аутентификация     | [PyJWT](https://pyjwt.readthedocs.io/) + [bcrypt](https://pypi.org/project/bcrypt/) |
| Геокодирование     | [geopy](https://geopy.readthedocs.io/) (Nominatim / OpenStreetMap) |
| Конфигурация       | [python-dotenv](https://pypi.org/project/python-dotenv/)       |
| ASGI-сервер        | [Uvicorn](https://www.uvicorn.org/)                             |

### Frontend

| Компонент       | Технология                                                        |
|-----------------|---------------------------------------------------------------------|
| UI-фреймворк    | [Vue 3](https://vuejs.org/) (глобальная сборка, Composition API)   |
| Стили           | [Pico.css v2](https://picocss.com/)                                 |
| HTTP-клиент     | [Axios](https://axios-http.com/)                                    |

Frontend не требует сборки — все зависимости подключаются через CDN (jsDelivr) прямо в `index.html`.

## Структура проекта

```
.
├── app/
│   ├── __init__.py
│   ├── main.py            # точка входа, создание таблиц, CORS, регистрация роутеров
│   ├── config.py          # загрузка настроек из .env
│   ├── database.py        # async engine, sessionmaker, Base
│   ├── dependencies.py    # DI: сессия БД, сервисы, текущий пользователь по токену
│   ├── enums.py           # роли пользователей (UserRole)
│   ├── models.py          # модели SQLAlchemy: User, GeoRecord, UserSession
│   ├── schemas.py         # Pydantic-схемы запросов/ответов
│   ├── auth.py            # создание и декодирование JWT (access/refresh)
│   ├── user_service.py    # бизнес-логика пользователей и сессий
│   ├── geo_service.py     # бизнес-логика геолокации (Nominatim, история)
│   └── routers/
│       ├── geo.py         # /geo/*
│       └── users.py       # /users/*
├── index.html              # весь frontend: разметка, стили, Vue-логика
├── requirements.txt
└── README.md
```

## Требования

- Python 3.11+
- PostgreSQL (локально или в контейнере)
- Современный браузер (для frontend)

## Установка и запуск backend

1. Склонируйте репозиторий и перейдите в его корень.

2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Создайте файл `.env` в корне проекта (рядом с папкой `app/`) со следующими переменными:

   ```env
   DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/<db_name>
   SECRET_KEY=change-me-to-a-long-random-string
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=change-me
   ```

   Таблицы в БД создаются автоматически при старте приложения (`Base.metadata.create_all`), отдельных миграций (Alembic) в проекте нет. Учётная запись администратора с ролью `admin` также создаётся автоматически при первом запуске, если пользователь с `ADMIN_EMAIL` ещё не существует.

5. Запустите сервер:
   ```bash
   uvicorn app.main:geo_app --reload --host 0.0.0.0 --port 8000
   ```

6. Документация Swagger UI будет доступна по адресу `http://127.0.0.1:8000/docs`.

## Запуск frontend

1. При необходимости отредактируйте адрес backend-сервера в `index.html`:
   ```js
   const API_URL = 'http://127.0.0.1:8000';
   ```
   Если backend запускается на другом хосте/порту (например, при доступе с другого устройства в локальной сети), укажите здесь актуальный IP-адрес и порт.

2. Откройте `index.html` в браузере (двойным кликом) или через любой локальный HTTP-сервер, например:
   ```bash
   npx serve .
   ```

Отдельная установка зависимостей для frontend не нужна — файл самодостаточен.

## API

| Метод | Путь                  | Назначение                                                            |
|-------|------------------------|-------------------------------------------------------------------------|
| GET   | `/`                    | Проверка, что сервис запущен                                            |
| POST  | `/users/`              | Регистрация нового пользователя (роль `user` по умолчанию)              |
| POST  | `/users/login`         | Вход (form-urlencoded: `username`, `password`), возвращает `access_token` и `refresh_token` |
| POST  | `/users/refresh`       | Обновление пары токенов по `refresh_token`                              |
| POST  | `/users/logout`        | Выход, инвалидация `refresh_token`                                      |
| GET   | `/geo/get_country`     | Определение страны по параметрам `lat`, `lon`, сохранение запроса в историю |
| GET   | `/geo/get_history`     | История запросов (админ видит все записи, юзер — только свои)           |

Все эндпоинты `/geo/*` требуют заголовок `Authorization: Bearer <access_token>`. На фронтенде токен подставляется автоматически через interceptor Axios.

> ⚠️ **Известная проблема.** Backend объявляет маршруты как `/users/` (со слэшем в конце) и `/geo/get_country` (без слэша), а frontend в `index.html` обращается к `/users` и `/geo/get_country/`. Из-за автоматических редиректов FastAPI (307) при таком несовпадении POST-запрос на регистрацию может терять тело запроса у некоторых HTTP-клиентов. Рекомендуется привести пути в `index.html` и в роутерах (`app/routers/*.py`) к единому виду.

## Аутентификация

- Access-токен — короткоживущий (по умолчанию 30 минут), используется для авторизации запросов.
- Refresh-токен — долгоживущий (по умолчанию 7 дней), хранится на backend в таблице `user_sessions` и используется одноразово: при обновлении старая запись удаляется, создаётся новая пара токенов.
- На frontend токены и данные пользователя (`user_email`, `user_role`) хранятся в `localStorage`.
- При получении `401 Unauthorized` interceptor Axios автоматически пытается обновить `access_token` через `/users/refresh` и повторяет исходный запрос.
- Если обновление токена не удалось — `localStorage` очищается и страница перезагружается.

## Роли пользователей

- `user` — видит и создаёт только свои записи истории.
- `admin` — видит записи всех пользователей. Первая учётная запись admin создаётся автоматически при старте backend из `ADMIN_EMAIL` / `ADMIN_PASSWORD`.

Роль на клиенте используется только для отображения и не является источником авторизации — все проверки прав выполняются на backend (см. `geo_service.get_history`).

## ⚠️ Замечания по безопасности

- Хранение JWT-токенов в `localStorage` уязвимо к XSS-атакам. Для продакшена рекомендуется рассмотреть `httpOnly`-cookies.
- `SECRET_KEY` и учётные данные администратора обязательно должны задаваться через `.env` и не попадать в репозиторий.
- `allow_origins=["*"]` в CORS-настройках (`app/main.py`) подходит для локальной разработки, но для продакшена список источников стоит сузить до конкретных доменов.
- В коде (`auth.py`, `dependencies.py`, `user_service.py`) присутствуют отладочные `print()` с фрагментами токенов — их стоит убрать или заменить на `logging` перед деплоем.
- Адрес API прописан в `index.html` в открытом виде — для разных окружений (dev/prod) стоит вынести его в конфигурацию.
- Nominatim (OpenStreetMap) имеет [политику использования](https://operations.osmfoundation.org/policies/nominatim/) с ограничением по частоте запросов — для высоконагруженного продакшена стоит рассмотреть собственный инстанс или платный геокодер.

## Локализация

Интерфейс и сообщения backend реализованы на русском языке (`lang="ru"`).
