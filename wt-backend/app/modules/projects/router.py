from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user_from_bearer
from app.modules.auth.oauth_models import OAuthAccount
from app.modules.auth.services import github_oauth
from app.modules.generate.service import generate_docker_files
from app.modules.generate.schemas import ProjectContext
from app.modules.projects.models import Project
from app.modules.projects.schemas import ProjectCreateRequest, ProjectResponse, ProjectSyncResponse

router = APIRouter(prefix="/projects", tags=["Projects"])

_MANIFEST_CANDIDATES = {
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "poetry.lock",
    "Pipfile",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "go.mod",
    "Cargo.toml",
    "Cargo.lock",
    "Gemfile",
}

_ENTRYPOINT_CANDIDATES = {
    "main.py",
    "app.py",
    "manage.py",
    "main.ts",
    "main.js",
    "server.ts",
    "server.js",
    "index.ts",
    "index.js",
    "main.go",
}

_STRUCTURE_PATH_LIMIT = 180
_CONTEXT_PATH_LIMIT = 120
_MANIFEST_CONTENT_LIMIT = 6000


@router.get("", response_model=list[ProjectResponse], summary="List user projects")
async def list_projects(
    user: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(user["id"])
    stmt = select(Project).where(Project.user_id == user_id).order_by(Project.created_at.desc())
    result = await db.execute(stmt)
    projects = list(result.scalars().all())
    return [
        ProjectResponse(
            id=p.id,
            github_repo_id=p.github_repo_id,
            name=p.name,
            full_name=p.full_name,
            html_url=p.html_url,
            default_branch=p.default_branch,
            selected_branch=p.selected_branch,
            created_at=p.created_at,
        )
        for p in projects
    ]


@router.post("/link", response_model=ProjectResponse, summary="Link project from GitHub repository")
async def link_project(
    body: ProjectCreateRequest,
    user: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(user["id"])
    stmt = select(Project).where(
        Project.user_id == user_id,
        Project.github_repo_id == body.github_repo_id,
        Project.selected_branch == (body.selected_branch or body.default_branch),
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This repository branch is already linked",
        )

    project = Project(
        user_id=user_id,
        github_repo_id=body.github_repo_id,
        name=body.name,
        full_name=body.full_name,
        html_url=body.html_url,
        default_branch=body.default_branch,
        selected_branch=body.selected_branch or body.default_branch,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse(
        id=project.id,
        github_repo_id=project.github_repo_id,
        name=project.name,
        full_name=project.full_name,
        html_url=project.html_url,
        default_branch=project.default_branch,
        selected_branch=project.selected_branch,
        created_at=project.created_at,
    )


@router.post("/{project_id}/sync-docker", response_model=ProjectSyncResponse, summary="Generate and commit Docker files")
async def sync_project_docker_files(
    project_id: str,
    user: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(user["id"])
    try:
        project_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project_id")

    project_stmt = select(Project).where(Project.id == project_uuid, Project.user_id == user_id)
    project_result = await db.execute(project_stmt)
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    oauth_stmt = (
        select(OAuthAccount)
        .where(OAuthAccount.user_id == user_id, OAuthAccount.provider == "github")
        .order_by(OAuthAccount.created_at.desc())
        .limit(1)
    )
    oauth_result = await db.execute(oauth_stmt)
    oauth = oauth_result.scalar_one_or_none()
    if not oauth:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub is not connected")

    access_token = (oauth.auth_metadata or {}).get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub access token is missing")

    branch = project.selected_branch or project.default_branch or "main"
    paths = await github_oauth.fetch_repository_tree(access_token, project.full_name, branch)
    compact_structure_paths = _select_relevant_paths(paths, limit=_STRUCTURE_PATH_LIMIT)
    project_structure = "\n".join(compact_structure_paths) if compact_structure_paths else "README.md"
    project_context = await _build_project_context(
        access_token=access_token,
        full_name=project.full_name,
        branch=branch,
        paths=compact_structure_paths,
    )

    files = generate_docker_files(
        project_structure=project_structure,
        format="tree",
        project_context=project_context,
    )

    committed_paths: list[str] = []
    for f in files:
        await github_oauth.upsert_repository_file(
            token=access_token,
            full_name=project.full_name,
            branch=branch,
            path=f.path,
            content=f.content,
            message=f"chore(whaletamer): update {f.path}",
        )
        committed_paths.append(f.path)

    return ProjectSyncResponse(
        project_id=project.id,
        branch=branch,
        committed_files=committed_paths,
    )


async def _build_project_context(
    access_token: str,
    full_name: str,
    branch: str,
    paths: list[str],
) -> ProjectContext:
    compact_context_paths = _select_relevant_paths(paths, limit=_CONTEXT_PATH_LIMIT)
    manifests: dict[str, str] = {}
    entrypoints: list[str] = []

    for path in compact_context_paths:
        base_name = path.rsplit("/", 1)[-1]
        if base_name in _MANIFEST_CANDIDATES:
            content = await github_oauth.fetch_repository_file_content(
                token=access_token,
                full_name=full_name,
                branch=branch,
                path=path,
            )
            if content and content.strip():
                manifests[path] = content[:_MANIFEST_CONTENT_LIMIT]

        if base_name in _ENTRYPOINT_CANDIDATES or path.endswith("/main.py") or path.endswith("/app/main.py"):
            entrypoints.append(path)

    return ProjectContext(
        paths=compact_context_paths,
        manifests=manifests,
        snippets={},
        entrypoints=sorted(set(entrypoints)),
        commands=[],
    )


def _select_relevant_paths(paths: list[str], limit: int) -> list[str]:
    ranked = sorted(set(paths), key=lambda path: (-_path_priority(path), path))
    selected = ranked[:limit]
    return sorted(selected)


def _path_priority(path: str) -> int:
    base_name = path.rsplit("/", 1)[-1]
    priority = 0

    if base_name in _MANIFEST_CANDIDATES:
        priority += 100
    if base_name in _ENTRYPOINT_CANDIDATES:
        priority += 90
    if path in {"Dockerfile", "docker-compose.yml", "docker-compose.yaml", "README.md"}:
        priority += 80
    if path.endswith("/Dockerfile") or path.endswith(".dockerignore"):
        priority += 70
    if path.startswith("src/"):
        priority += 50
    if path.startswith("app/"):
        priority += 45
    if path.startswith("cmd/") or path.startswith("crates/") or path.startswith("packages/"):
        priority += 40
    if base_name in {"main.rs", "lib.rs", "mod.rs", "main.go", "package.json", "tsconfig.json"}:
        priority += 35
    if "/migrations/" in path or path.startswith("migrations/"):
        priority += 20
    if path.count("/") <= 1:
        priority += 15

    return priority
