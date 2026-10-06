# PsycheLog Personal Diary

Backend API для PsycheLog.

## Настройка backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Конфигурация окружения

1. Скопируй пример файла окружения:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Для запуска тестов скопируй `.env` в `.env.test` и измени название базы данных на тестовую:

   ```powershell
   Copy-Item .env .env.test
   ```

   В `.env.test` измени как минимум:

   ```ini
   ENVIRONMENT=test
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/psychelog_test
   ```

   Остальные значения (пароли, секреты, адреса) подставь под своё локальное окружение.

   Никогда не коммить `.env` и `.env.test` в Git. В репозитории должен быть только `.env.example`.

## Запуск PostgreSQL через Docker

Из корня проекта:

```powershell
wsl
sourse .venv/bin/activate
docker compose up -d postgres
```

Это запустит PostgreSQL на `localhost:5432`.

Дождись готовности контейнера, затем создай базы данных:

```powershell
docker exec -it <имя_контейнера_postgres> psql -U postgres -c "CREATE DATABASE psychelog;"
docker exec -it <имя_контейнера_postgres> psql -U postgres -c "CREATE DATABASE psychelog_test;"
```

Замени `<имя_контейнера_postgres>` на реальное имя контейнера (например, `project_root-postgres-1`).

Обнови `.env` и `.env.test`:

```ini
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/psychelog
```

```ini
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/psychelog_test
```

## Запуск тестов

Из каталога `backend`:

```powershell
python -m pytest tests -v
```

С отчётом по покрытию:

```powershell
python -m pytest tests --cov=app --cov-branch --cov-report=term-missing
```

Тесты используют конфигурацию из `.env.test`.

## Запуск API

Из каталога `backend`:

```powershell
uvicorn app.main:app --reload
```

Документация API:

```text
http://127.0.0.1:8000/docs
```

## Запуск всего стека через Docker (опционально)

Из корня проекта:

```powershell
docker compose up --build
```

Это запустит PostgreSQL и backend API согласно `docker-compose.yml`.