import re
from dataclasses import asdict, dataclass, field

from app.modules.generate.schemas import ProjectContext


@dataclass(slots=True)
class InfrastructureDependency:
    name: str
    confidence: str
    reason: str


@dataclass(slots=True)
class ProjectAnalysis:
    stack: str
    language: str
    framework: str | None = None
    package_manager: str | None = None
    runtime_entrypoint: str | None = None
    infrastructure: list[InfrastructureDependency] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_log_dict(self) -> dict[str, object]:
        return {
            "stack": self.stack,
            "language": self.language,
            "framework": self.framework,
            "package_manager": self.package_manager,
            "runtime_entrypoint": self.runtime_entrypoint,
            "infrastructure": [asdict(item) for item in self.infrastructure],
            "notes": self.notes,
        }


def analyze_project_context(project_context: ProjectContext | None) -> ProjectAnalysis:
    if project_context is None:
        return ProjectAnalysis(
            stack="unknown",
            language="unknown",
            notes=["Project context is empty; analyzer could not infer stack."],
        )

    manifests = project_context.manifests or {}
    paths = project_context.paths or []
    entrypoints = project_context.entrypoints or []
    merged_text = _merged_context_text(project_context)

    if _is_frontend_backend_monorepo(manifests, paths):
        return ProjectAnalysis(
            stack="fullstack",
            language="multi",
            framework="frontend-backend",
            runtime_entrypoint=_pick_entrypoint(entrypoints, ("backend/main.py", "backend/app.py", "backend/src/main.rs", "backend/main.go")),
            infrastructure=_detect_infrastructure(merged_text),
            notes=_collect_notes(project_context, "fullstack"),
        )

    if _has_manifest(manifests, "Cargo.toml"):
        return ProjectAnalysis(
            stack="rust",
            language="rust",
            package_manager="cargo",
            runtime_entrypoint=_pick_entrypoint(entrypoints, ("src/main.rs", "main.rs")),
            infrastructure=_detect_infrastructure(merged_text),
            notes=_collect_notes(project_context, "rust"),
        )

    if _has_manifest(manifests, "go.mod"):
        return ProjectAnalysis(
            stack="go",
            language="go",
            package_manager="go",
            runtime_entrypoint=_pick_entrypoint(entrypoints, ("main.go",)),
            infrastructure=_detect_infrastructure(merged_text),
            notes=_collect_notes(project_context, "go"),
        )

    if _has_manifest(manifests, "package.json"):
        framework = _detect_node_framework(manifests, merged_text)
        package_manager = _detect_node_package_manager(paths)
        return ProjectAnalysis(
            stack=framework or "node",
            language="node",
            framework=framework,
            package_manager=package_manager,
            runtime_entrypoint=_pick_entrypoint(entrypoints, ("main.ts", "main.js", "server.ts", "server.js", "index.ts", "index.js")),
            infrastructure=_detect_infrastructure(merged_text),
            notes=_collect_notes(project_context, framework or "node"),
        )

    if _has_python_manifest(manifests):
        framework = _detect_python_framework(manifests, merged_text)
        package_manager = _detect_python_package_manager(manifests)
        return ProjectAnalysis(
            stack=framework or "python",
            language="python",
            framework=framework,
            package_manager=package_manager,
            runtime_entrypoint=_pick_entrypoint(entrypoints, ("main.py", "app.py", "manage.py")),
            infrastructure=_detect_infrastructure(merged_text),
            notes=_collect_notes(project_context, framework or "python"),
        )

    return ProjectAnalysis(
        stack="unknown",
        language="unknown",
        runtime_entrypoint=entrypoints[0] if entrypoints else None,
        infrastructure=_detect_infrastructure(merged_text),
        notes=["Analyzer could not match the project to a supported local stack."],
    )


def _has_manifest(manifests: dict[str, str], file_name: str) -> bool:
    return any(path.endswith(file_name) for path in manifests)


def _has_python_manifest(manifests: dict[str, str]) -> bool:
    return any(
        path.endswith(name)
        for path in manifests
        for name in ("pyproject.toml", "requirements.txt", "Pipfile", "poetry.lock")
    )


def _has_prefixed_manifest(manifests: dict[str, str], prefix: str, file_names: tuple[str, ...]) -> bool:
    return any(path.startswith(prefix) and path.endswith(name) for path in manifests for name in file_names)


def _is_frontend_backend_monorepo(manifests: dict[str, str], paths: list[str]) -> bool:
    has_frontend = _has_prefixed_manifest(manifests, "frontend/", ("package.json",))
    has_backend = (
        _has_prefixed_manifest(manifests, "backend/", ("Cargo.toml", "go.mod", "pyproject.toml", "requirements.txt", "package.json"))
        or any(
            path.startswith("backend/")
            and path.endswith(name)
            for path in paths
            for name in ("Cargo.toml", "go.mod", "pyproject.toml", "requirements.txt", "package.json")
        )
    )
    return has_frontend and has_backend


def _detect_node_framework(manifests: dict[str, str], merged_text: str) -> str | None:
    package_json = next((content for path, content in manifests.items() if path.endswith("package.json")), "")
    lowered = f"{package_json}\n{merged_text}".lower()
    if '"express"' in lowered or "'express'" in lowered or re.search(r"\bexpress\b", lowered):
        return "express"
    if '"next"' in lowered or "'next'" in lowered:
        return "nextjs"
    if '"nest"' in lowered or "'@nestjs/core'" in lowered:
        return "nestjs"
    return None


def _detect_python_framework(manifests: dict[str, str], merged_text: str) -> str | None:
    lowered = f"{''.join(manifests.values())}\n{merged_text}".lower()
    if "fastapi" in lowered:
        return "fastapi"
    if "django" in lowered:
        return "django"
    if "flask" in lowered:
        return "flask"
    return None


def _detect_node_package_manager(paths: list[str]) -> str:
    if any(path.endswith("pnpm-lock.yaml") for path in paths):
        return "pnpm"
    if any(path.endswith("yarn.lock") for path in paths):
        return "yarn"
    return "npm"


def _detect_python_package_manager(manifests: dict[str, str]) -> str:
    if _has_manifest(manifests, "poetry.lock"):
        return "poetry"
    if _has_manifest(manifests, "Pipfile"):
        return "pipenv"
    pyproject = next((content for path, content in manifests.items() if path.endswith("pyproject.toml")), "")
    if "tool.uv" in pyproject or "uvicorn" in pyproject or "uv" in pyproject:
        return "uv"
    return "pip"


def _pick_entrypoint(entrypoints: list[str], preferred_suffixes: tuple[str, ...]) -> str | None:
    for suffix in preferred_suffixes:
        for entrypoint in entrypoints:
            if entrypoint.endswith(suffix):
                return entrypoint
    return entrypoints[0] if entrypoints else None


def _detect_infrastructure(merged_text: str) -> list[InfrastructureDependency]:
    lowered = merged_text.lower()
    detected: list[InfrastructureDependency] = []

    def add(name: str, confidence: str, reason: str) -> None:
        if any(item.name == name for item in detected):
            return
        detected.append(InfrastructureDependency(name=name, confidence=confidence, reason=reason))

    postgres_dependency_signals = (
        "postgresql",
        "asyncpg",
        "psycopg",
        'features = ["postgres"',
        "sqlx",
        "tokio-postgres",
        "diesel",
        "postgres",
    )
    postgres_runtime_signals = (
        "postgres_host",
        "postgres_db",
        "database_url=postgres",
        "database_url = postgres",
        "postgres://",
        "postgresql://",
    )
    if any(signal in lowered for signal in postgres_dependency_signals + postgres_runtime_signals):
        confidence = "high" if any(signal in lowered for signal in postgres_runtime_signals) else "medium"
        add("postgres", confidence, "Detected PostgreSQL driver or configuration keys.")

    redis_dependency_signals = (
        "ioredis",
        "redis.asyncio",
        "bullmq",
        "celery[redis]",
        "redis",
        "go-redis",
    )
    redis_runtime_signals = (
        "redis_url",
        "redis_host",
        "redis://",
    )
    if any(signal in lowered for signal in redis_dependency_signals + redis_runtime_signals):
        confidence = "high" if any(signal in lowered for signal in redis_runtime_signals) else "medium"
        add("redis", confidence, "Detected Redis client or configuration keys.")

    minio_dependency_signals = (
        "boto3",
        "minio",
        "s3fs",
        'boto3.client("s3"',
        "aws-sdk/client-s3",
        "@aws-sdk/client-s3",
        "aws-sdk-s3",
    )
    minio_runtime_signals = (
        "minio(",
        "minio_endpoint",
        "s3_endpoint",
        "endpoint_url",
        "aws_endpoint_url",
        "s3-compatible",
    )
    if any(signal in lowered for signal in minio_dependency_signals + minio_runtime_signals):
        confidence = "high" if any(signal in lowered for signal in minio_runtime_signals) else "medium"
        add("minio", confidence, "Detected MinIO/S3-compatible storage configuration.")

    return detected


def _collect_notes(project_context: ProjectContext, stack: str) -> list[str]:
    notes: list[str] = []
    if stack == "rust" and not any(path.endswith("Cargo.lock") for path in project_context.paths):
        notes.append("Cargo.lock not found; build reproducibility may be reduced.")
    if stack == "fastapi" and not any("--factory" in command for command in project_context.commands):
        notes.append("FastAPI detected; verify whether app should run with --factory.")
    if stack == "fullstack":
        notes.append("Detected frontend/backend monorepo; generated separate service Dockerfiles.")
    return notes


def _merged_context_text(project_context: ProjectContext) -> str:
    parts: list[str] = []
    parts.extend(project_context.paths or [])
    parts.extend((project_context.manifests or {}).values())
    parts.extend((project_context.snippets or {}).values())
    parts.extend(project_context.entrypoints or [])
    parts.extend(project_context.commands or [])
    return "\n".join(parts)
