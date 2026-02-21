from fastapi import APIRouter, Depends

from app.modules.auth.dependencies import get_current_user_from_bearer
from app.modules.generate.schemas import GenerateRequest, GenerateResponse
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
