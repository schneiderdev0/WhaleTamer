from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_payload
from app.modules.auth.integration_models import IntegrationType
from app.modules.auth.services import integration_tokens as integration_tokens_service
from app.modules.auth.dependencies import get_current_user_from_bearer
from app.modules.collector.models import CollectorEvent
from app.modules.collector.schemas import CollectorIngestRequest, CollectorIngestResponse, DataCollectorTokenResponse

router = APIRouter(prefix="/collector", tags=["Collector"])


@router.post("/token", response_model=DataCollectorTokenResponse, summary="Create Data Collector token")
async def create_data_collector_token(
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(payload["id"])
    plain, _record = await integration_tokens_service.create_integration_token(
        user_id=user_id,
        type_=IntegrationType.DATA_COLLECTOR,
        status="active",
        metadata={},
        db=db,
    )
    return DataCollectorTokenResponse(token=plain)


@router.post("/ingest", response_model=CollectorIngestResponse, summary="Ingest data from Data Collector")
async def ingest_data(
    body: CollectorIngestRequest,
    user_payload: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(user_payload["id"])
    event = CollectorEvent(
        user_id=user_id,
        source=body.source,
        payload=body.payload.model_dump(),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return CollectorIngestResponse(id=str(event.id))

