# 🧠 PsycheLog — Personal Diary & Mental Mentor

Backend API для закрытого мобильного приложения эмоциональной самопомощи, личного дневника и ИИ-медиации конфликтов.

> **Статус:** MVP в активной разработке (Спринт 5 завершён ✅)
> **Платформы:** Android и iOS
> **Аудитория:** 18+, закрытый круг друзей, пар и небольших групп
> **Монетизация:** Отсутствует

---

## 🎯 О проекте

PsycheLog помогает пользователям:

- Выговориться при злости, тревоге, обиде или эмоциональной перегрузке
- Не принимать решения и не отправлять сообщения сгоряча
- Вести личный дневник текстом или голосом
- Сохранять полный диалог либо краткое AI-резюме
- Видеть субъективную недельную динамику
- Общаться с близкими в личных и групповых чатах
- Переводить конфликт в режим ИИ-медиации, где участники не читают эмоциональные исходные сообщения друг друга

⚠️ **Важно:** Приложение не является медицинским сервисом. Оно не ставит диагнозов, не заменяет психотерапевта, врача, психолога или экстренные службы.

---

## 🛠️ Технологический стек

### Backend

- **Язык:** Python 3.11+
- **Фреймворк:** FastAPI (асинхронный REST API + WebSocket)
- **База данных:** PostgreSQL 14 (через SQLAlchemy + asyncpg)
- **Миграции:** Alembic
- **Кэш и Rate Limiting:** Redis 7
- **Очереди задач:** RabbitMQ 3 + Celery
- **Хранилище медиа:** MinIO (S3-compatible, для локальной разработки)
- **Тестирование:** pytest, pytest-asyncio, httpx TestClient

### Frontend (в разработке)

- **Фреймворк:** Flutter 3.x
- **State Management:** Riverpod / BLoC
- **Networking:** Dio + WebSocket
- **Local Storage:** Hive / SharedPreferences
- **Security:** flutter_secure_storage

---

## 🚀 Быстрый старт (Рекомендуемый способ через Docker)

Этот способ поднимает всё окружение (PostgreSQL, Redis, RabbitMQ, MinIO, API, Celery) одной командой.

### 1. Клонируйте репозиторий и перейдите в него:

```bash
git clone <your-repo-url>
cd project_root
```

### 2. Создайте файл окружения из шаблона:

```bash
cp .env.example .env
```

Откройте `.env` и при необходимости измените секреты. Для локальной разработки значения по умолчанию работают.

### 3. Запустите весь стек:

```bash
docker compose up -d --build
```

Первый запуск может занять 2-3 минуты (Docker скачает образы и соберёт backend).

### 4. Примените миграции базы данных:

```bash
docker compose exec api alembic upgrade head
```

### 5. Проверьте работоспособность:

- **API Docs (Swagger):** <http://localhost:8000/docs>
- **Health Check:** <http://localhost:8000/health>
- **Readiness Check:** <http://localhost:8000/ready>
- **MinIO Console:** <http://localhost:9001> (логин: `minioadmin`, пароль: `replace_me`)
- **RabbitMQ Management:** <http://localhost:15672> (логин: `app_user`, пароль: `app_password`)

---

## 💻 Локальная разработка (Без Docker для API)

Если вы хотите запускать FastAPI локально через `uvicorn` (например, для отладки в IDE):

### 1. Запустите только инфраструктуру через Docker:

```bash
docker compose up -d postgres redis rabbitmq minio
```

### 2. Создайте и активируйте виртуальное окружение:

```bash
# Windows (PowerShell)
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS / Linux / WSL
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Установите зависимости:

```bash
pip install -r requirements.txt
```

### 4. Настройте окружение:

Создайте файл `backend/.env` на основе `.env.example`, но измените хосты на `localhost`:

```env
DATABASE_URL=postgresql+asyncpg://app_user:app_password@localhost:5432/app_db
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://app_user:app_password@localhost:5672/app_vhost
S3_ENDPOINT_URL=http://localhost:9000
```

### 5. Примените миграции:

```bash
alembic upgrade head
```

### 6. Запустите сервер разработки:

```bash
uvicorn app.main:app --reload
```

API будет доступен по адресу: <http://localhost:8000/docs>

---

## 🧪 Тестирование

Проект использует `pytest` с изолированной конфигурацией для тестов.

### Подготовка тестового окружения

1. Убедитесь, что в папке `backend/` существует файл `.env.test` (он не должен коммититься в Git).
2. Создайте его на основе `.env.example`, указав тестовую базу данных:

```env
ENVIRONMENT=test
DATABASE_URL=postgresql+asyncpg://app_user:app_password@localhost:5432/psychelog_test
```

### Запуск тестов

```bash
cd backend
python -m pytest tests/ -v
```

### Запуск с отчётом о покрытии кода:

```bash
python -m pytest tests/ --cov=app --cov-branch --cov-report=term-missing
```

### Запуск конкретных тестов:

```bash
# Только тесты аутентификации
python -m pytest tests/integration/api/test_auth.py -v

# Только тесты дневника
python -m pytest tests/integration/api/test_diary.py -v
```

---

## 📂 Структура проекта

```text
project_root/
├── README.md                       # Этот файл
├── .gitignore                      # Игнорируемые файлы
├── .editorconfig                   # Настройки редактора
├── .env.example                    # Шаблон переменных окружения
├── docker-compose.yml              # Конфигурация Docker Compose
│
├── docs/                           # Документация
│   ├── architecture.md
│   ├── api.md
│   ├── ai-providers.md
│   ├── privacy-and-consents.md
│   ├── mediation-state-machine.md
│   └── deployment.md
│
├── .github/
│   └── workflows/                  # CI/CD пайплайны
│       ├── backend-ci.yml
│       └── frontend-ci.yml
│
├── Frontend/                       # Flutter-клиент (в разработке)
│   ├── lib/
│   │   ├── core/                   # Ядро приложения
│   │   ├── features/               # Фичи приложения
│   │   ├── local_storage/          # Локальный кэш
│   │   └── main.dart               # Точка входа
│   ├── test/                       # Unit-тесты
│   ├── integration_test/           # Интеграционные тесты
│   ├── assets/                     # Ресурсы
│   └── pubspec.yaml                # Зависимости Flutter
│
└── Backend/                        # FastAPI backend
    ├── app/
    │   ├── api/v1/                 # HTTP и WebSocket endpoints
    │   ├── ai/                     # AI-провайдеры
    │   ├── core/                   # Ядро приложения
    │   ├── models/                 # SQLAlchemy ORM модели
    │   ├── schemas/                # Pydantic схемы
    │   ├── services/               # Бизнес-логика
    │   ├── repositories/           # Запросы к БД
    │   ├── workers/                # Celery задачи
    │   └── main.py                 # Точка входа FastAPI
    │
    ├── alembic/                    # Миграции базы данных
    ├── tests/                      # Тесты
    ├── Dockerfile                  # Docker образ для backend
    ├── requirements.txt            # Зависимости Python
    ├── requirements-dev.txt        # Dev-зависимости
    ├── pyproject.toml              # Конфигурация инструментов
    └── .env.example                # Шаблон переменных окружения
```

---

## 🔐 Безопасность и приватность

### Ключевые принципы:

1. **Безопасность пользователя:** ИИ не ставит диагнозов и не выступает судьёй конфликта
2. **Согласие до обработки:** Кэш и облачный AI работают только после явного согласия
3. **Минимизация хранения:** Исходные голосовые и видео удаляются через 7 дней
4. **Контроль у пользователя:** Можно выбрать, что сохранить, отредактировать резюме, очистить кэш, экспортировать и удалить данные
5. **Не раскрывать конфликт:** В медиации исходные эмоциональные сообщения не становятся публичными

### Технические меры:

- Хеширование PIN через bcrypt или Argon2id
- Короткоживущие JWT access token и refresh token с возможностью отзыва
- Rate limiting для регистрации, входа, OTP, инвайтов, загрузок и WebSocket
- Проверка прав доступа к дневнику, сообщениям, группам и медиации на сервере
- Защита от IDOR (Insecure Direct Object References)
- Параметризованные SQLAlchemy-запросы (защита от SQL injection)
- Presigned URL для медиа
- HTTPS, CORS allowlist, security headers
- Секреты только в environment variables
- Структурированные логи без текста дневников, сообщений медиации, PIN, OTP, JWT

---

## 📊 Что реализовано 

- ✅ Docker Compose с PostgreSQL, Redis, RabbitMQ, MinIO
- ✅ FastAPI skeleton с health checks
- ✅ Аутентификация: регистрация, login, PIN, JWT, refresh sessions
- ✅ OTP для восстановления доступа
- ✅ Машина состояний блокировки PIN (3 ошибки → заморозка, 4 ошибки → жёсткая блокировка)
- ✅ Интеграционные тесты для auth (35 тестов, все проходят)
- ✅ Alembic миграции для базовой схемы БД

---

## 🗺️ План разработки

### Спринт 2: Профиль и согласия ✅

- ✅Эндпоинты обновления профиля (имя, никнейм, аватар)
- ✅Управление тремя обязательными согласиями
- ✅Логика отзыва согласий
- ✅Безопасное удаление аккаунта (soft delete + очистка сессий)

### Спринт 3: Дневник и стабилизация ✅

- ✅CRUD записей дневника
- ✅AI-резюме и редактирование
- ✅Режим "Стабилизация"
- ✅AI provider abstraction (Gemini/Groq/Ollama fallback)

### Спринт 4: Голос и медиа ✅

- ✅Presigned upload URL
- ✅Голосовые и короткие видео
- Whisper транскрибация(не доделал, пока заглушка)
- ✅Celery задачи для обработки
- ✅Автоудаление исходных медиа через 7 дней

### Спринт 5: Обычные чаты

- ✅Личные и групповые чаты
- ✅Роль создателя, инвайты
- ✅Сообщения, удаление своих сообщений
- ✅WebSocket, reconnect, delivery/read states
- ✅Push-уведомления

### Спринт 6: Медиация

- State machine медиации
- Единогласное согласие
- Слепая зона
- Приватные рекомендации
- Подтверждение общего итога

### Спринт 7: Качество и деплой

- Нагрузочные и security tests
- Backup и restore check
- CI/CD пайплайны
- Закрытый deployment на Render

---