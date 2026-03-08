from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CollectorPayload(BaseModel):
    """Общий формат данных от агента.

    Делаем структуру достаточно гибкой, чтобы не переписывать контракт
    при эволюции Data Collector.
    """

    hostname: str = Field(..., description="Имя сервера/хоста")
    timestamp: datetime = Field(..., description="Время формирования пакета на стороне агента")
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Произвольные метрики (CPU, RAM, диск, сеть и т.п.)",
    )
    logs: dict[str, str] = Field(
        default_factory=dict,
        description="Ключ – идентификатор/путь лога, значение – текст (например, хвост файла)",
    )


class CollectorIngestRequest(BaseModel):
    source: str = Field(..., description="Идентификатор инстанса агента или сервиса")
    payload: CollectorPayload


class CollectorIngestResponse(BaseModel):
    id: str
    status: str = "accepted"


class DataCollectorTokenResponse(BaseModel):
    token: str  # показываем один раз

