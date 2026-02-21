from pydantic import BaseModel, Field


class ProjectContext(BaseModel):
    paths: list[str] = Field(default_factory=list)
    manifests: dict[str, str] = Field(default_factory=dict)
    entrypoints: list[str] = Field(default_factory=list)
    commands: list[str] = Field(default_factory=list)


class GenerateRequest(BaseModel):
    project_structure: str = Field(..., description="Project structure in tree or markdown format")
    format: str = Field(default="tree", description="Format of structure: tree | markdown")
    project_context: ProjectContext | None = None


class FileContent(BaseModel):
    path: str
    content: str


class GenerateResponse(BaseModel):
    files: list[FileContent]
