from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.dependencies import get_current_user_from_bearer
from app.core.database import get_db
from app.modules.generate.models import GenerateJob, GeneratedFile, GenerateJobStatus
from app.modules.generate.schemas import (
    FileContent,
    GenerateJobCreateResponse,
    GenerateJobStatusResponse,
    GenerateRequest,
    GenerateResponse,
)
from app.modules.generate.service import generate_docker_files

router = APIRouter(tags=["Generate"])


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    body: GenerateRequest,
    _user: dict = Depends(get_current_user_from_bearer),
):
    files = generate_docker_files(
        project_structure=body.project_structure,
        format=body.format or "tree",
        project_context=body.project_context,
    )
    return GenerateResponse(files=files)


@router.post("/generate/jobs", response_model=GenerateJobCreateResponse, summary="Create generation job (stores history)")
async def create_generate_job(
    body: GenerateRequest,
    user: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(user["id"])
    job = GenerateJob(
        user_id=user_id,
        status=GenerateJobStatus.PENDING.value,
        request=body.model_dump(),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    try:
        files = generate_docker_files(
            project_structure=body.project_structure,
            format=body.format or "tree",
            project_context=body.project_context,
        )
        job.status = GenerateJobStatus.COMPLETED.value
        for f in files:
            db.add(GeneratedFile(job_id=job.id, path=f.path, content=f.content))
        await db.commit()
    except Exception as exc:
        job.status = GenerateJobStatus.FAILED.value
        job.error = str(exc)
        await db.commit()
    return GenerateJobCreateResponse(job_id=str(job.id), status=job.status)


@router.get("/generate/jobs/{job_id}", response_model=GenerateJobStatusResponse, summary="Get generation job status/result")
async def get_generate_job(
    job_id: str,
    user: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(user["id"])
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job_id")

    stmt = select(GenerateJob).where(GenerateJob.id == job_uuid, GenerateJob.user_id == user_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    files = [FileContent(path=f.path, content=f.content) for f in (job.files or [])]
    return GenerateJobStatusResponse(
        job_id=str(job.id),
        status=job.status,
        error=job.error,
        files=files,
    )
