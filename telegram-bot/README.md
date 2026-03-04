# Whale Tamer Telegram Bot

Telegram-бот на Go, который:
- привязывает Telegram чат к пользователю по токену `tg_...`
- показывает последний отчёт с краткой сводкой и рекомендациями
- позволяет читать/менять настройки уведомлений
- поддерживает `long polling` и `webhook`

## ENV

- `WT_TG_BOT_TOKEN` — токен Telegram бота
- `WT_BACKEND_URL` — например `http://backend:8000`
- `WT_BOT_STATE_PATH` — путь к файлу состояния (по умолчанию `/data/state.json`)
- `WT_TG_UPDATE_MODE` — `polling` (default) или `webhook`
- `WT_TG_WEBHOOK_URL` — публичный URL webhook (обязательно для `webhook` режима)
- `WT_TG_WEBHOOK_LISTEN_ADDR` — адрес HTTP-сервера для webhook (default `:8080`)
- `WT_TG_WEBHOOK_PATH` — путь локального webhook-handler (default `/`)

## Команды

- `/start <tg_token>` — привязка (бот вызывает backend `POST /telegram/link`)
- `/latest` — получить последний отчёт (бот вызывает backend `GET /telegram/reports/latest` с `Authorization: Bearer tg_...`)
- `/notify` — показать настройки уведомлений
- `/notify <all|critical> <event|hourly|daily> [on|off]` — изменить настройки уведомлений
