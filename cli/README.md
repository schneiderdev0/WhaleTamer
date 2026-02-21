# Whale Tamer CLI

CLI утилита для автоматизации создания Dockerfile и docker-compose на основе структуры проекта.

## Как запустить

**Через Go (без сборки):**
```bash
cd cli
go run .
# или с аргументами:
go run . --token YOUR_TOKEN generate
```

**Сборка бинарника:**
```bash
cd cli
go build -o wt .
./wt --token YOUR_TOKEN generate
```

По умолчанию запросы идут на `http://localhost:8000`. Для другого бекенда: `--api https://your-api.com` или переменная окружения `WHALETAMER_API_URL`.

## Использование

### Авторизация

Используется **постоянный CLI-токен** (не JWT с сайта). Его создаёт авторизованный пользователь на сайте: `POST /auth/cli-tokens` (Bearer JWT), в ответ приходит `token` — его один раз вводят в CLI. CLI сохраняет токен в `~/.config/whaletamer/token` (или `%APPDATA%\whaletamer\token` на Windows) и в следующих запусках подставляет автоматически.

Токен можно также задать флагом `--token` / `-t` или переменной окружения `WHALETAMER_TOKEN`. Перед выполнением команд токен проверяется запросом `POST /auth/cli-tokens/verify` с телом `{"token": "..."}`. Базовый URL по умолчанию — `http://localhost:8000`; можно изменить флагом `--api` или переменной `WHALETAMER_API_URL`.

### Команда `generate`

Собирает структуру проекта (дерево или Markdown), при необходимости сохраняет её в файл, отправляет на `POST /generate` и создаёт полученные Dockerfile и docker-compose файлы.

```bash
# Токен и генерация (структура не сохраняется в файл)
./wt --token YOUR_TOKEN generate

# Сохранить структуру в MD
./wt -t YOUR_TOKEN generate --save-structure project-structure.md --format markdown

# Сохранить структуру в текстовый файл (дерево)
./wt -t YOUR_TOKEN generate -s structure.txt -f tree

# Указать корень проекта и свой API
./wt --token YOUR_TOKEN --api https://your-backend.example.com generate -p ./myapp
```

### Флаги `generate`

| Флаг | Короткий | Описание |
|------|----------|----------|
| `--format` | `-f` | Формат структуры: `tree` или `markdown` |
| `--save-structure` | `-s` | Путь к файлу для сохранения структуры (опционально) |
| `--project-root` | `-p` | Корень проекта (по умолчанию текущая директория) |

## API (бекенд)

- **Создание CLI-токена:** `POST /auth/cli-tokens` с заголовком `Authorization: Bearer <jwt>` (JWT с сайта). Тело опционально: `{"name": "название"}`. В ответе — `token` (показать один раз).
- **Проверка CLI-токена:** `POST /auth/cli-tokens/verify` с телом `{"token": "<cli_token>"}`. Ожидается 200 OK и `user_id`, `email`.
- **Список CLI-токенов:** `GET /auth/cli-tokens` с заголовком `Authorization: Bearer <jwt>`. Список токенов пользователя (без самого токена).
- **Генерация:** `POST /generate` с заголовком `Authorization: Bearer <cli_token>` (или JWT) и телом:
  ```json
  {
    "project_structure": "<текст дерева или markdown>",
    "format": "tree"
  }
  ```
  Ответ:
  ```json
  {
    "files": [
      { "path": "Dockerfile", "content": "..." },
      { "path": "docker-compose.yaml", "content": "..." }
    ]
  }
  ```
  Пути в `path` задаются относительно корня проекта; CLI создаёт директории при необходимости.
