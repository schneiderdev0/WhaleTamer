from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProjectCreateRequest(BaseModel):
    github_repo_id: int
    name: str
    full_name: str
    html_url: str
    default_branch: str = "main"
    selected_branch: str = "main"


class ProjectResponse(BaseModel):
    id: UUID
    github_repo_id: int
    name: str
    full_name: str
    html_url: str
    default_branch: str
    selected_branch: str
    created_at: datetime


class ProjectSyncResponse(BaseModel):
    project_id: UUID
    branch: str
    committed_files: list[str]
