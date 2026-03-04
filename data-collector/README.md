# Whale Tamer Data Collector

Минимальный агент для отправки метрик на backend.

## ENV

- `WT_BACKEND_URL` — например `http://backend:8000`
- `WT_DC_TOKEN` — токен вида `dc_...` (получить через backend `POST /collector/token`)
- `WT_SOURCE` — идентификатор агента (по умолчанию hostname)
- `WT_INTERVAL_SECONDS` — период отправки, по умолчанию `15`

## Endpoint

Шлёт `POST /collector/ingest` с `Authorization: Bearer dc_...`.

