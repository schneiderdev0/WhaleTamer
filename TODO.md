# Описание проекта
Whale Tamer - сервис для автоматизации создания Docker контейнеров, сбора логов и создания отчетов о состоянии сервера. 

## Проект состоит из следующих модулей:
1. Frontend сайт на React.
2. Backend на FastAPI с интеграцией с Gemini.
3. CLI инструмент на Golang.
4. Модуль сборки логов и показаний сервера клиента на Golang в контейнере Docker (Data Collector).
5. Телеграм бот для отправки отчетов пользователю на Golang.

## Существует два пользовательских пути:
1. Через сайт:
- Пользователь авторизируется через GitHub.
- Сайт получает доступ к репозиторию и создает все необходимые Dockerfile, docker-compose.yaml для проекта и с контейнером для Data Collector. Вносит коммит в репозиторий.
2. Через CLI: 
- Пользователь авторизируется на сайте.
- Получает токен для CLI инструмента.
- Пользователь авторизируется в CLI с помощью токена и вводит команду wt generate.
- CLI создает все нужные Dockerfile, docker-compose.yaml для проекта и с контейнером для Data Collector.

## После запуска
После того как пользователь запустил свои контейнеры на сервере Data Collector отправляет данные на сервер, Бекенд отправляет данные в Gemini для получения отчета, вывода и советов. Фронтенд выводит данные для пользователя.

Если пользователь подключил себе Telegram бота, тогда отчеты отправляются и в чат бота.

# Задачи


### Обновление статуса (последние выполненные задачи)
- ✅ Frontend: доработан OAuth callback — вход теперь успешен при наличии `token` и `user_id`, даже если `email` отсутствует.
- ✅ Frontend: в `Telegram Settings` добавлено управление настройками уведомлений (`enabled`, `frequency`, `severity`) с загрузкой и сохранением через backend API.
- ✅ Frontend: расширены RU/EN i18n-ключи для блока Telegram-уведомлений.

## Frontend
- (P1) Реализовать базовое приложение на React+TypeScript с маршрутизацией (страницы: главная, авторизация, дашборд проектов, страница статуса генерации Docker-конфигурации, страница отчетов). ✅
- (P1) Настроить авторизацию через GitHub (OAuth) и хранение сессии пользователя, интеграция с backend API. ✅
- (P2) Создать UI-флоу по выбору репозитория/ветки и запуску генерации Dockerfile/docker-compose (через вызовы backend `generate`-модулей). ✅ (базовый флоу через структуру проекта)
- (P2) Реализовать страницу просмотра отчетов по серверам/контейнерам: список проектов, детализация по каждому запуску (состояние, логи, рекомендации). ✅
- (P3) Добавить интеграцию с Telegram ботом в личном кабинете (подключение/отключение, отображение статуса). ✅ (страница настроек Telegram)
- (P3) Настроить i18n, темы и базовый дизайн с использованием Tailwind, shadcn и кастомных хуков (useAPI/useTheme/useLanguage и т.д.). ✅
- (P3) Добавить обработку ошибок и уведомления (React-toastify) для всех критичных действий: авторизация, запуск генерации, подключения Telegram, просмотр отчетов). ✅

## Backend
- (P1) Спроектировать и доработать модели БД для пользователей, привязки к GitHub, CLI-токенов, интеграционных токенов для Data Collector и Telegram. ✅
- (P1) Реализовать полный цикл авторизации через GitHub (получение кода, обмен на токен, привязка аккаунта к пользователю). ✅
- (P1) Настроить конфигурацию (settings), безопасность (JWT/сессии, CORS), логирование и базовую observability (метрики/health-checkи). ✅
- (P1) Реализовать API для приёма данных от Data Collector (аутентификация по токену, валидация входных данных, буферизация и сохранение в БД). ✅
- (P1) Завершить и расширить модуль `generate`: эндпоинты для запуска генерации Dockerfile/docker-compose, статусы задач, хранение истории генераций. ✅
- (P2) Добавить слой интеграции с Gemini: формирование промптов на основе логов/метрик, получение и сохранение отчетов и рекомендаций. ✅
- (P2) Добавить API для Telegram бота: выдача отчетов по запросу бота, Webhook/long polling обработчики (в зависимости от архитектуры). ✅
- (P2) Подготовить Dockerfile и docker-compose для backend, dev/prod окружений и миграций БД. ✅

## Data Collector
- (P1) Спроектировать агент на Go, работающий внутри Docker-контейнера, для сбора логов и метрик (CPU, RAM, диск, сеть, состояние контейнеров/сервисов). ✅
- (P1) Реализовать конфигурацию Data Collector (env-переменные или config-файл): адрес backend, токен, частота отправки данных, фильтры по сервисам. ✅
- (P1) Реализовать клиент для отправки данных в backend (аутентификация по токену, сериализация данных, обработка ответов и ошибок). ✅
- (P2) Добавить надежную доставку данных: ретраи, бэкоф, буферизация при недоступности сети/серверов. ✅ (ретраи + экспоненциальный бэкоф)
- (P2) Минимизировать нагрузку: продумать объем собираемых данных, интервалы, ограничения по размеру пакетов. ✅ (интервалы и ограничение набора метрик)
- (P2) Подготовить Dockerfile и пример docker-compose-сервиса для интеграции Data Collector в пользовательский проект. ✅

## Telegram Bot
- (P2) Спроектировать структуру бота на Go: обработчики команд (`/start`, `/help`, связывание аккаунта, просмотр последних отчетов), обработка callback-кнопок. ✅
- (P2) Реализовать процесс привязки Telegram аккаунта к пользователю (генерация/подтверждение токена через сайт или backend). ✅
- (P2) Настроить получение обновлений (Webhook или long polling), обработку ошибок и повторов запросов. ✅
- (P3) Реализовать форматированные уведомления: отправка кратких отчетов по состоянию серверов/контейнеров и детальных рекомендаций от Gemini. ✅
- (P3) Добавить настройки частоты/типа уведомлений (критические/все, по расписанию/по событию) и хранить их на backend. ✅
- (P3) Подготовить Dockerfile и конфигурацию для деплоя бота (токен бота, URL Webhook, окружения). ✅

## Итоговый отчет и следующие шаги (2026-03-04)

### Итог
- Все задачи из этого файла завершены: `27/27` пунктов отмечены как выполненные.
- Дальше нужно выполнить стандартный цикл: установить зависимости, прогнать проверки и поднять весь стек.

### 1. Предварительные требования
- Docker + Docker Compose v2
- Go `1.22+`
- Python `3.14+` и `uv`
- Node.js `20+` и Corepack (для Yarn `4.5.1`)

### 2. Установка зависимостей

```bash
# backend
cd backend
uv sync --frozen

# frontend
cd ../frontend
corepack enable
yarn install --immutable

# cli
cd ../cli
go mod download

# data-collector
cd ../data-collector
go mod download

# telegram-bot
cd ../telegram-bot
go mod download
```

### 3. Минимальная конфигурация backend (`backend/.env`)

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=dev_db
POSTGRES_USER=root
POSTGRES_PASSWORD=qwerty

JWT_SECRET_KEY=change_me
GEMINI_API_KEY=your_gemini_key

GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback
FRONTEND_BASE_URL=http://localhost:5173

# Пример для локальной разработки:
BACKEND_CORS_ORIGINS=["http://localhost:5173"]
```

### 4. Прогон проверок/тестов

```bash
# backend (проверка импортов и синтаксиса)
cd backend
uv run python -m compileall app

# frontend
cd ../frontend
yarn lint
yarn build

# go-модули (в репозитории пока нет *_test.go, но go test проверяет сборку)
cd ../cli && go test ./...
cd ../data-collector && go test ./...
cd ../telegram-bot && go test ./...
```

### 5. Запуск всех элементов проекта (локальный dev-сценарий)

1. Запустить БД, миграции и backend:

```bash
cd backend
docker compose -f docker-compose-dev.yaml up --build
```

2. Запустить frontend (в отдельном терминале):

```bash
cd frontend
yarn dev
```

3. Получить токены (после авторизации и получения JWT пользователя):

```bash
# Data Collector token
curl -X POST http://localhost:8000/collector/token \
  -H "Authorization: Bearer <JWT>"

# Telegram link token
curl -X POST http://localhost:8000/telegram/link-token \
  -H "Authorization: Bearer <JWT>"

# CLI token
curl -X POST http://localhost:8000/auth/cli-tokens \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

4. Запустить Data Collector (в отдельном терминале):

```bash
cd data-collector
WT_BACKEND_URL=http://localhost:8000 \
WT_DC_TOKEN=<DC_TOKEN> \
WT_SOURCE=dev-local \
WT_INTERVAL_SECONDS=15 \
go run .
```

5. Запустить Telegram Bot (в отдельном терминале):

```bash
cd telegram-bot
WT_TG_BOT_TOKEN=<BOT_TOKEN> \
WT_BACKEND_URL=http://localhost:8000 \
WT_TG_UPDATE_MODE=polling \
go run .
```

6. Проверить CLI-флоу генерации (в отдельном терминале):

```bash
cd cli
go run . token set <CLI_TOKEN>
go run . generate -p /path/to/your/project
```
