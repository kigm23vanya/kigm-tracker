# Kigm Tracker

Kigm Tracker - это MVP-скелет full-stack системы для учета учебной активности студентов колледжа: задания, оценки, достижения, участие в мероприятиях и лидерборды.

## Что уже есть в проекте

- Backend на FastAPI с базовой доменной моделью и REST API.
- Frontend на Next.js с тремя ключевыми экранами: Main Menu, Profile, Leaderboard.
- Подготовленная интеграционная граница для синхронизации данных Google Classroom.
- Базовая бизнес-логика для рейтингов и активности.
- Документация по архитектуре, API и плану реализации.

## Структура репозитория

```text
.
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  │  ├─ deps.py
│  │  │  └─ routers/
│  │  │     ├─ auth.py
│  │  │     ├─ profile.py
│  │  │     ├─ assignments.py
│  │  │     ├─ events.py
│  │  │     ├─ achievements.py
│  │  │     ├─ leaderboard.py
│  │  │     └─ sync.py
│  │  ├─ core/
│  │  │  ├─ config.py
│  │  │  └─ database.py
│  │  ├─ db/
│  │  │  └─ bootstrap.py
│  │  ├─ models/
│  │  │  └─ core.py
│  │  ├─ schemas/
│  │  │  └─ api.py
│  │  ├─ services/
│  │  │  ├─ activity.py
│  │  │  ├─ achievements.py
│  │  │  ├─ leaderboard.py
│  │  │  └─ classroom_sync.py
│  │  └─ main.py
│  ├─ .env.example
│  └─ requirements.txt
├─ frontend/
│  ├─ app/
│  │  ├─ layout.tsx
│  │  ├─ page.tsx
│  │  ├─ profile/
│  │  │  └─ page.tsx
│  │  └─ leaderboard/
│  │     └─ page.tsx
│  ├─ components/
│  │  ├─ NavBar.tsx
│  │  └─ SectionCard.tsx
│  ├─ lib/
│  │  ├─ api.ts
│  │  └─ types.ts
│  ├─ .env.example
│  ├─ package.json
│  ├─ next.config.mjs
│  └─ tsconfig.json
├─ docs/
│  ├─ architecture.md
│  ├─ api-mapping.md
│  └─ implementation-plan.md
├─ docker-compose.yml
└─ README.md
```

## Пояснение по модулям

### Backend

- app/api/routers - HTTP-эндпоинты по предметным разделам (auth, profile, assignments, events, leaderboard, sync).
- app/schemas - контракты запросов и ответов API (Pydantic-схемы).
- app/models - ORM-модели локальной базы данных.
- app/services - бизнес-логика (лидерборды, достижения, активность, синхронизация Classroom).
- app/core - конфиг приложения и подключение к базе.
- app/db/bootstrap.py - первичное создание/инициализация данных.

### Frontend

- app/page.tsx - главный экран с лентами событий и заданий.
- app/profile/page.tsx - профиль студента: достижения, оценки, участие в мероприятиях.
- app/leaderboard/page.tsx - рейтинги по отметкам, активности и достижениям.
- components - переиспользуемые UI-компоненты.
- lib/api.ts - клиент для вызова backend API.
- lib/types.ts - типы данных фронтенда.

### Docs

- architecture.md - целевая архитектура и слои системы.
- api-mapping.md - карта ТЗ к API-эндпоинтам.
- implementation-plan.md - поэтапный план разработки.

## Покрытие MVP из ТЗ

- Авторизация через Google: точки входа /auth/google и /auth/me (каркас потока).
- Профиль студента: базовые данные, достижения, оценки, участие в мероприятиях.
- Лента мероприятий и лента заданий/оценок.
- Три лидерборда: по отметкам, активности и достижениям.
- Фильтры области сравнения: group, course, college.
- Эндпоинты синхронизации Classroom для начальной и периодической загрузки.

## Быстрый старт

### 1. Поднять PostgreSQL (рекомендуется)

Из корня проекта:

```bash
docker compose up -d
```

### 2. Запуск backend

1. Создать и активировать виртуальное окружение Python.
2. Установить зависимости:

```bash
pip install -r backend/requirements.txt
```

3. Создать env-файл:

```bash
copy backend/.env.example backend/.env
```

4. Запустить API:

```bash
uvicorn app.main:app --reload --app-dir backend
```

Backend будет доступен по адресу: http://localhost:8000

### 3. Запуск frontend

1. Установить зависимости:

```bash
cd frontend
npm install
```

2. Создать env-файл:

```bash
copy .env.example .env
```

3. Запустить dev-сервер:

```bash
npm run dev
```

Frontend будет доступен по адресу: http://localhost:3000

## Переменные окружения

### Backend (.env)

- DATABASE_URL=postgresql+psycopg://kigm:kigm@localhost:5432/kigm_tracker
- APP_ENV=development
- APP_NAME=Kigm Tracker API

### Frontend (.env)

- NEXT_PUBLIC_API_URL=http://localhost:8000
- NEXT_PUBLIC_USER_ID=2

## Важные замечания

- Интеграция с Google Classroom в текущей версии реализована как сервисный слой для MVP и дальнейшего подключения реального API.
- Для продакшн-интеграции потребуется настроить Google Cloud Project, OAuth consent screen и корректные scopes.
- При недоступности Classroom следует использовать локально сохраненные данные и стратегию повторных попыток.
