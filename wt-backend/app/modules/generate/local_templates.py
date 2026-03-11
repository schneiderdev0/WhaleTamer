import json
import re

from app.modules.generate.analyzer import InfrastructureDependency, ProjectAnalysis, analyze_project_context
from app.modules.generate.schemas import FileContent, ProjectContext


def generate_local_files(analysis: ProjectAnalysis, project_context: ProjectContext | None) -> list[FileContent] | None:
    if project_context is None:
        return None
    if analysis.stack == "fullstack":
        return _generate_fullstack_files(project_context)
    if analysis.stack == "rust":
        return _with_compose(
            analysis,
            project_context,
            [FileContent(path="Dockerfile", content=_render_rust_dockerfile(project_context))],
        )
    if analysis.stack == "express":
        return _with_compose(
            analysis,
            project_context,
            [FileContent(path="Dockerfile", content=_render_express_dockerfile(project_context, analysis))],
        )
    if analysis.stack == "fastapi":
        return _with_compose(
            analysis,
            project_context,
            [FileContent(path="Dockerfile", content=_render_fastapi_dockerfile(project_context, analysis))],
        )
    if analysis.stack == "django":
        return _with_compose(
            analysis,
            project_context,
            [FileContent(path="Dockerfile", content=_render_django_dockerfile(project_context, analysis))],
        )
    if analysis.stack == "flask":
        return _with_compose(
            analysis,
            project_context,
            [FileContent(path="Dockerfile", content=_render_flask_dockerfile(project_context, analysis))],
        )
    if analysis.stack == "go":
        return _with_compose(
            analysis,
            project_context,
            [FileContent(path="Dockerfile", content=_render_go_dockerfile(project_context))],
        )
    return None


def _generate_fullstack_files(project_context: ProjectContext) -> list[FileContent] | None:
    frontend_context = _subcontext(project_context, "frontend/")
    backend_context = _subcontext(project_context, "backend/")
    if frontend_context is None or backend_context is None:
        return None

    frontend_analysis = analyze_project_context(frontend_context)
    backend_analysis = analyze_project_context(backend_context)
    if frontend_analysis.stack not in {"express", "node", "nextjs", "nestjs"}:
        return None

    backend_dockerfile = _render_backend_dockerfile_for_analysis(backend_context, backend_analysis)
    if backend_dockerfile is None:
        return None

    frontend_dockerfile = _render_prefixed_node_dockerfile(frontend_context, frontend_analysis, "frontend")
    compose = _render_fullstack_compose(frontend_analysis, backend_analysis)
    return [
        FileContent(path="frontend/Dockerfile", content=frontend_dockerfile),
        FileContent(path="backend/Dockerfile", content=backend_dockerfile),
        FileContent(path="docker-compose.yaml", content=compose),
    ]


def _with_compose(
    analysis: ProjectAnalysis,
    project_context: ProjectContext,
    files: list[FileContent],
) -> list[FileContent]:
    compose = _render_compose(analysis, project_context)
    return files + [FileContent(path="docker-compose.yaml", content=compose)]


def _render_rust_dockerfile(project_context: ProjectContext) -> str:
    binary_name = _extract_rust_binary_name(project_context) or "app"
    return f"""FROM rust:1.86-bookworm AS builder
WORKDIR /app

COPY Cargo.toml Cargo.lock* ./
COPY src ./src

RUN cargo build --release

FROM debian:bookworm-slim AS runtime
WORKDIR /app

RUN apt-get update \\
    && apt-get install -y --no-install-recommends ca-certificates libssl3 \\
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/{binary_name} /usr/local/bin/{binary_name}

EXPOSE 8080

CMD ["/usr/local/bin/{binary_name}"]
"""


def _render_express_dockerfile(project_context: ProjectContext, analysis: ProjectAnalysis) -> str:
    package_manager = analysis.package_manager or "npm"
    install_cmd = {
        "pnpm": "corepack enable && pnpm install --frozen-lockfile",
        "yarn": "corepack enable && yarn install --frozen-lockfile",
        "npm": "npm ci",
    }.get(package_manager, "npm ci")
    build_cmd = _extract_package_script(project_context, "build")
    start_cmd = _extract_node_start_command(project_context)
    build_section = f"RUN {build_cmd}\n\n" if build_cmd else ""

    return f"""FROM node:22-bookworm-slim AS base
WORKDIR /app

COPY package.json ./
COPY package-lock.json* pnpm-lock.yaml* yarn.lock* ./

RUN {install_cmd}

COPY . .

{build_section}EXPOSE 3000

CMD {json.dumps(start_cmd)}
"""


def _render_fastapi_dockerfile(project_context: ProjectContext, analysis: ProjectAnalysis) -> str:
    package_manager = analysis.package_manager or "pip"
    runtime_cmd = _extract_fastapi_command(project_context)

    if package_manager == "uv":
        install_section = """COPY pyproject.toml ./
COPY uv.lock* ./

RUN pip install --no-cache-dir uv \\
    && uv sync --frozen --no-dev
"""
        runtime = json.dumps(runtime_cmd if runtime_cmd[:2] == ["sh", "-c"] else ["uv", "run", *runtime_cmd])
    elif package_manager == "poetry":
        install_section = """COPY pyproject.toml poetry.lock* ./

RUN pip install --no-cache-dir poetry \\
    && poetry config virtualenvs.create false \\
    && poetry install --only main --no-root
"""
        runtime = json.dumps(runtime_cmd)
    else:
        install_section = """COPY requirements.txt* ./
COPY pyproject.toml* ./

RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
"""
        runtime = json.dumps(runtime_cmd)

    return f"""FROM python:3.12-bookworm AS base
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

{install_section}
COPY . .

EXPOSE 8000

CMD {runtime}
"""


def _render_go_dockerfile(project_context: ProjectContext) -> str:
    binary_name = _extract_go_binary_name(project_context) or "app"
    entry_target = _extract_go_build_target(project_context)
    return f"""FROM golang:1.24-bookworm AS builder
WORKDIR /app

COPY go.mod go.sum* ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/{binary_name} {entry_target}

FROM debian:bookworm-slim AS runtime
WORKDIR /app

RUN apt-get update \\
    && apt-get install -y --no-install-recommends ca-certificates \\
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /out/{binary_name} /usr/local/bin/{binary_name}

EXPOSE 8080

CMD ["/usr/local/bin/{binary_name}"]
"""


def _render_django_dockerfile(project_context: ProjectContext, analysis: ProjectAnalysis) -> str:
    package_manager = analysis.package_manager or "pip"
    runtime_cmd = _extract_django_command(project_context)

    if package_manager == "uv":
        install_section = """COPY pyproject.toml ./
COPY uv.lock* ./

RUN pip install --no-cache-dir uv \\
    && uv sync --frozen --no-dev
"""
        runtime = json.dumps(runtime_cmd if runtime_cmd[:2] == ["sh", "-c"] else ["uv", "run", *runtime_cmd])
    elif package_manager == "poetry":
        install_section = """COPY pyproject.toml poetry.lock* ./

RUN pip install --no-cache-dir poetry \\
    && poetry config virtualenvs.create false \\
    && poetry install --only main --no-root
"""
        runtime = json.dumps(runtime_cmd)
    else:
        install_section = """COPY requirements.txt* ./
COPY pyproject.toml* ./

RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
"""
        runtime = json.dumps(runtime_cmd)

    manage_py = _extract_django_manage_path(project_context)
    collectstatic_cmd = f"python {manage_py} collectstatic --noinput || true" if manage_py else "true"

    return f"""FROM python:3.12-bookworm AS base
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

{install_section}
COPY . .

RUN {collectstatic_cmd}

EXPOSE 8000

CMD {runtime}
"""


def _render_flask_dockerfile(project_context: ProjectContext, analysis: ProjectAnalysis) -> str:
    package_manager = analysis.package_manager or "pip"
    runtime_cmd = _extract_flask_command(project_context)

    if package_manager == "uv":
        install_section = """COPY pyproject.toml ./
COPY uv.lock* ./

RUN pip install --no-cache-dir uv \\
    && uv sync --frozen --no-dev
"""
        runtime = json.dumps(runtime_cmd if runtime_cmd[:2] == ["sh", "-c"] else ["uv", "run", *runtime_cmd])
    elif package_manager == "poetry":
        install_section = """COPY pyproject.toml poetry.lock* ./

RUN pip install --no-cache-dir poetry \\
    && poetry config virtualenvs.create false \\
    && poetry install --only main --no-root
"""
        runtime = json.dumps(runtime_cmd)
    else:
        install_section = """COPY requirements.txt* ./
COPY pyproject.toml* ./

RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
"""
        runtime = json.dumps(runtime_cmd)

    return f"""FROM python:3.12-bookworm AS base
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

{install_section}
COPY . .

EXPOSE 8000

CMD {runtime}
"""


def _render_backend_dockerfile_for_analysis(project_context: ProjectContext, analysis: ProjectAnalysis) -> str | None:
    if analysis.stack == "rust":
        return _render_rust_dockerfile_prefixed(project_context, "backend")
    if analysis.stack == "go":
        return _render_go_dockerfile_prefixed(project_context, "backend")
    if analysis.stack == "fastapi":
        return _render_python_dockerfile_prefixed(project_context, analysis, "backend", kind="fastapi")
    if analysis.stack == "django":
        return _render_python_dockerfile_prefixed(project_context, analysis, "backend", kind="django")
    if analysis.stack == "flask":
        return _render_python_dockerfile_prefixed(project_context, analysis, "backend", kind="flask")
    if analysis.stack in {"express", "node", "nextjs", "nestjs"}:
        return _render_prefixed_node_dockerfile(project_context, analysis, "backend")
    return None


def _extract_rust_binary_name(project_context: ProjectContext) -> str | None:
    cargo_toml = next((content for path, content in project_context.manifests.items() if path.endswith("Cargo.toml")), "")
    if not cargo_toml:
        return None
    package_match = re.search(r'(?ms)^\[package\].*?^name\s*=\s*"([^"]+)"', cargo_toml)
    if package_match:
        return package_match.group(1).replace("-", "_")
    bin_match = re.search(r'(?ms)^\[\[bin\]\].*?^name\s*=\s*"([^"]+)"', cargo_toml)
    if bin_match:
        return bin_match.group(1)
    return None


def _extract_package_script(project_context: ProjectContext, script_name: str) -> str | None:
    package_json = next((content for path, content in project_context.manifests.items() if path.endswith("package.json")), "")
    if not package_json:
        return None
    try:
        data = json.loads(package_json)
    except json.JSONDecodeError:
        return None
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return None
    value = scripts.get(script_name)
    return value if isinstance(value, str) and value.strip() else None


def _extract_node_start_command(project_context: ProjectContext) -> list[str]:
    start_script = _extract_package_script(project_context, "start")
    if start_script:
        return ["sh", "-c", start_script]
    if any(path.endswith("dist/server.js") for path in project_context.paths):
        return ["node", "dist/server.js"]
    if any(path.endswith("server.js") for path in project_context.paths):
        return ["node", "server.js"]
    if any(path.endswith("src/server.ts") for path in project_context.paths):
        return ["npm", "run", "start"]
    return ["node", "index.js"]


def _extract_fastapi_command(project_context: ProjectContext) -> list[str]:
    commands = project_context.commands or []
    for command in commands:
        if "uvicorn" in command:
            return ["sh", "-c", command]
    if any(path.endswith("app/main.py") for path in project_context.paths):
        return ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    if any(path.endswith("main.py") for path in project_context.paths):
        return ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    return ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]


def _extract_go_binary_name(project_context: ProjectContext) -> str | None:
    go_mod = next((content for path, content in project_context.manifests.items() if path.endswith("go.mod")), "")
    if not go_mod:
        return None
    module_match = re.search(r"(?m)^module\s+([^\s]+)", go_mod)
    if not module_match:
        return None
    module_name = module_match.group(1).rstrip("/")
    return module_name.split("/")[-1].replace("-", "_")


def _extract_go_build_target(project_context: ProjectContext) -> str:
    if any(path == "cmd/main.go" or path.endswith("/cmd/main.go") for path in project_context.paths):
        return "./cmd"
    if any(path.startswith("cmd/") and path.endswith("main.go") for path in project_context.paths):
        cmd_targets = sorted({path.split("/")[1] for path in project_context.paths if path.startswith("cmd/") and path.endswith("main.go")})
        if len(cmd_targets) == 1:
            return f"./cmd/{cmd_targets[0]}"
    return "."


def _extract_django_manage_path(project_context: ProjectContext) -> str | None:
    for path in project_context.paths:
        if path.endswith("manage.py"):
            return path
    return None


def _extract_django_command(project_context: ProjectContext) -> list[str]:
    manage_py = _extract_django_manage_path(project_context)
    project_module = _extract_django_project_module(project_context)
    if project_module:
        return ["gunicorn", f"{project_module}.wsgi:application", "--bind", "0.0.0.0:8000"]
    if manage_py:
        return ["python", manage_py, "runserver", "0.0.0.0:8000"]
    return ["gunicorn", "app.wsgi:application", "--bind", "0.0.0.0:8000"]


def _extract_django_project_module(project_context: ProjectContext) -> str | None:
    for path in project_context.paths:
        if path.endswith("/wsgi.py"):
            parts = path.split("/")
            if len(parts) >= 2:
                return parts[-2]
    return None


def _extract_flask_command(project_context: ProjectContext) -> list[str]:
    for command in project_context.commands or []:
        if "gunicorn" in command:
            return ["sh", "-c", command]
    if any(path.endswith("app.py") for path in project_context.paths):
        return ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
    if any(path.endswith("main.py") for path in project_context.paths):
        return ["gunicorn", "main:app", "--bind", "0.0.0.0:8000"]
    return ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]


def _render_compose(analysis: ProjectAnalysis, project_context: ProjectContext) -> str:
    port = _default_port(analysis)
    infra = _selected_infrastructure(analysis.infrastructure)
    advisory = _advisory_infrastructure(analysis.infrastructure)
    depends_on = [item.name for item in infra]
    app_env = _app_environment(infra)

    lines: list[str] = ["services:", "  app:", "    build:", "      context: .", "      dockerfile: Dockerfile"]
    lines.extend([f"    ports:", f'      - "{port}:{port}"'])
    if depends_on:
        lines.append("    depends_on:")
        for service_name in depends_on:
            lines.append(f"      - {service_name}")
    if app_env:
        lines.append("    environment:")
        for key, value in app_env.items():
            lines.append(f"      {key}: {value}")

    for item in infra:
        lines.extend(_render_infra_service(item))

    if advisory:
        lines.append("")
        lines.append("# Advisory dependencies detected but not auto-added:")
        for item in advisory:
            lines.append(f"# - {item.name}: {item.reason} (confidence: {item.confidence})")

    if infra:
        lines.append("volumes:")
        for item in infra:
            if item.name == "postgres":
                lines.append("  postgres_data:")
            if item.name == "minio":
                lines.append("  minio_data:")

    return "\n".join(lines) + "\n"


def _render_fullstack_compose(frontend_analysis: ProjectAnalysis, backend_analysis: ProjectAnalysis) -> str:
    backend_port = _default_port(backend_analysis)
    frontend_port = 3000
    infra = _selected_infrastructure(backend_analysis.infrastructure)
    advisory = _advisory_infrastructure(backend_analysis.infrastructure)
    backend_env = _app_environment(infra)

    lines: list[str] = [
        "services:",
        "  frontend:",
        "    build:",
        "      context: .",
        "      dockerfile: frontend/Dockerfile",
        "    ports:",
        f'      - "{frontend_port}:{frontend_port}"',
        "    depends_on:",
        "      - backend",
        "  backend:",
        "    build:",
        "      context: .",
        "      dockerfile: backend/Dockerfile",
        "    ports:",
        f'      - "{backend_port}:{backend_port}"',
    ]
    if infra:
        lines.append("    depends_on:")
        lines.extend([f"      - {item.name}" for item in infra])
    if backend_env:
        lines.append("    environment:")
        for key, value in backend_env.items():
            lines.append(f"      {key}: {value}")

    for item in infra:
        lines.extend(_render_infra_service(item))

    if advisory:
        lines.append("")
        lines.append("# Advisory dependencies detected but not auto-added:")
        for item in advisory:
            lines.append(f"# - {item.name}: {item.reason} (confidence: {item.confidence})")

    if infra:
        lines.append("volumes:")
        for item in infra:
            if item.name == "postgres":
                lines.append("  postgres_data:")
            if item.name == "minio":
                lines.append("  minio_data:")

    return "\n".join(lines) + "\n"


def _default_port(analysis: ProjectAnalysis) -> int:
    if analysis.stack == "express":
        return 3000
    if analysis.stack in {"rust", "fastapi", "django", "flask"}:
        return 8000
    if analysis.stack == "go":
        return 8080
    return 8080


def _selected_infrastructure(items: list[InfrastructureDependency]) -> list[InfrastructureDependency]:
    return [item for item in items if item.confidence == "high"]


def _advisory_infrastructure(items: list[InfrastructureDependency]) -> list[InfrastructureDependency]:
    return [item for item in items if item.confidence == "medium"]


def _app_environment(items: list[InfrastructureDependency]) -> dict[str, str]:
    env: dict[str, str] = {}
    names = {item.name for item in items}
    if "postgres" in names:
        env.update(
            {
                "POSTGRES_HOST": "postgres",
                "POSTGRES_USER": "postgres",
                "POSTGRES_PASSWORD": "postgres",
                "POSTGRES_DB": "app",
                "DATABASE_URL": "postgresql://postgres:postgres@postgres:5432/app",
            }
        )
    if "redis" in names:
        env.update(
            {
                "REDIS_HOST": "redis",
                "REDIS_URL": "redis://redis:6379/0",
            }
        )
    if "minio" in names:
        env.update(
            {
                "MINIO_ENDPOINT": "minio:9000",
                "AWS_ACCESS_KEY_ID": "minioadmin",
                "AWS_SECRET_ACCESS_KEY": "minioadmin",
                "AWS_REGION": "us-east-1",
            }
        )
    return env


def _render_infra_service(item: InfrastructureDependency) -> list[str]:
    if item.name == "postgres":
        return [
            "  postgres:",
            "    image: postgres:17-bookworm",
            "    environment:",
            "      POSTGRES_USER: postgres",
            "      POSTGRES_PASSWORD: postgres",
            "      POSTGRES_DB: app",
            "    ports:",
            '      - "5432:5432"',
            "    volumes:",
            "      - postgres_data:/var/lib/postgresql/data",
        ]
    if item.name == "redis":
        return [
            "  redis:",
            "    image: redis:7-bookworm",
            "    ports:",
            '      - "6379:6379"',
        ]
    if item.name == "minio":
        return [
            "  minio:",
            "    image: minio/minio:RELEASE.2025-02-28T09-55-16Z",
            "    command: server /data --console-address :9001",
            "    environment:",
            "      MINIO_ROOT_USER: minioadmin",
            "      MINIO_ROOT_PASSWORD: minioadmin",
            "    ports:",
            '      - "9000:9000"',
            '      - "9001:9001"',
            "    volumes:",
            "      - minio_data:/data",
        ]
    return []


def _subcontext(project_context: ProjectContext, prefix: str) -> ProjectContext | None:
    def strip_prefix(value: str) -> str:
        return value[len(prefix):]

    paths = [strip_prefix(path) for path in project_context.paths if path.startswith(prefix)]
    manifests = {strip_prefix(path): content for path, content in project_context.manifests.items() if path.startswith(prefix)}
    snippets = {strip_prefix(path): content for path, content in project_context.snippets.items() if path.startswith(prefix)}
    entrypoints = [strip_prefix(path) for path in project_context.entrypoints if path.startswith(prefix)]
    if not paths and not manifests:
        return None
    return ProjectContext(paths=paths, manifests=manifests, snippets=snippets, entrypoints=entrypoints, commands=project_context.commands)


def _render_prefixed_node_dockerfile(project_context: ProjectContext, analysis: ProjectAnalysis, prefix: str) -> str:
    package_manager = analysis.package_manager or "npm"
    install_cmd = {
        "pnpm": "corepack enable && pnpm install --frozen-lockfile",
        "yarn": "corepack enable && yarn install --frozen-lockfile",
        "npm": "npm ci",
    }.get(package_manager, "npm ci")
    build_cmd = _extract_package_script(project_context, "build")
    start_cmd = _extract_node_start_command(project_context)
    build_section = f"RUN cd /app/{prefix} && {build_cmd}\n\n" if build_cmd else ""

    return f"""FROM node:22-bookworm-slim AS base
WORKDIR /app/{prefix}

COPY {prefix}/package.json ./package.json
COPY {prefix}/package-lock.json* {prefix}/pnpm-lock.yaml* {prefix}/yarn.lock* ./

RUN {install_cmd}

COPY {prefix} ./

{build_section}EXPOSE 3000

CMD {json.dumps(start_cmd)}
"""


def _render_rust_dockerfile_prefixed(project_context: ProjectContext, prefix: str) -> str:
    binary_name = _extract_rust_binary_name(project_context) or "app"
    return f"""FROM rust:1.86-bookworm AS builder
WORKDIR /app

COPY {prefix}/Cargo.toml {prefix}/Cargo.lock* ./
COPY {prefix}/src ./src

RUN cargo build --release

FROM debian:bookworm-slim AS runtime
WORKDIR /app

RUN apt-get update \\
    && apt-get install -y --no-install-recommends ca-certificates libssl3 \\
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/{binary_name} /usr/local/bin/{binary_name}

EXPOSE 8080

CMD ["/usr/local/bin/{binary_name}"]
"""


def _render_go_dockerfile_prefixed(project_context: ProjectContext, prefix: str) -> str:
    binary_name = _extract_go_binary_name(project_context) or "app"
    entry_target = _extract_go_build_target(project_context)
    entry_target = entry_target if entry_target == "." else entry_target
    build_target = f"./{entry_target.lstrip('./')}" if entry_target != "." else "."
    return f"""FROM golang:1.24-bookworm AS builder
WORKDIR /app/{prefix}

COPY {prefix}/go.mod {prefix}/go.sum* ./
RUN go mod download

COPY {prefix} ./

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/{binary_name} {build_target}

FROM debian:bookworm-slim AS runtime
WORKDIR /app

RUN apt-get update \\
    && apt-get install -y --no-install-recommends ca-certificates \\
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /out/{binary_name} /usr/local/bin/{binary_name}

EXPOSE 8080

CMD ["/usr/local/bin/{binary_name}"]
"""


def _render_python_dockerfile_prefixed(
    project_context: ProjectContext,
    analysis: ProjectAnalysis,
    prefix: str,
    kind: str,
) -> str:
    package_manager = analysis.package_manager or "pip"
    if kind == "fastapi":
        runtime_cmd = _extract_fastapi_command(project_context)
    elif kind == "django":
        runtime_cmd = _extract_django_command(project_context)
    else:
        runtime_cmd = _extract_flask_command(project_context)

    if package_manager == "uv":
        install_section = f"""COPY {prefix}/pyproject.toml ./pyproject.toml
COPY {prefix}/uv.lock* ./

RUN pip install --no-cache-dir uv \\
    && uv sync --frozen --no-dev
"""
        runtime = json.dumps(runtime_cmd if runtime_cmd[:2] == ["sh", "-c"] else ["uv", "run", *runtime_cmd])
    elif package_manager == "poetry":
        install_section = f"""COPY {prefix}/pyproject.toml ./pyproject.toml
COPY {prefix}/poetry.lock* ./

RUN pip install --no-cache-dir poetry \\
    && poetry config virtualenvs.create false \\
    && poetry install --only main --no-root
"""
        runtime = json.dumps(runtime_cmd)
    else:
        install_section = f"""COPY {prefix}/requirements.txt* ./
COPY {prefix}/pyproject.toml* ./

RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
"""
        runtime = json.dumps(runtime_cmd)

    after_copy = ""
    if kind == "django":
        manage_py = _extract_django_manage_path(project_context)
        collectstatic_cmd = f"python {manage_py} collectstatic --noinput || true" if manage_py else "true"
        after_copy = f"RUN {collectstatic_cmd}\n\n"

    return f"""FROM python:3.12-bookworm AS base
WORKDIR /app/{prefix}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

{install_section}COPY {prefix} ./

{after_copy}EXPOSE 8000

CMD {runtime}
"""
