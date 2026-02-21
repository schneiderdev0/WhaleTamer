import json
import re
import shlex
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from google import genai

from app.core.settings import s
from app.modules.generate.schemas import FileContent, ProjectContext

GEMINI_MODEL = "gemini-2.5-flash"
MAX_ATTEMPTS = 3

PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "stack": {"type": "string"},
        "services": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "path": {"type": "string"},
                    "language": {"type": "string"},
                    "framework": {"type": "string"},
                    "entrypoint": {"type": "string"},
                    "runtime_command": {"type": "string"},
                    "port": {"type": "integer"},
                    "needs_dockerfile": {"type": "boolean"},
                    "needs_compose": {"type": "boolean"},
                },
                "required": [
                    "name",
                    "path",
                    "language",
                    "framework",
                    "entrypoint",
                    "runtime_command",
                    "needs_dockerfile",
                    "needs_compose",
                ],
            },
        },
        "notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["stack", "services", "notes"],
}

FILES_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "files": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        }
    },
    "required": ["files"],
}

_PLAN_PROMPT_TEMPLATE = """You are a senior DevOps assistant.

Create a concise execution plan for Docker setup.
Return JSON only, shaped by schema.

Project structure (format: {format}):
---
{project_structure}
---

Structured context:
{context_json}

Rules for planning:
1) Infer services from context and file paths, do not invent services that are not supported by files.
2) Select realistic runtime command based on manifests/scripts/entrypoints.
3) If context implies FastAPI app factory, include uvicorn command with --factory.
4) If Python project uses uv lock workflow, prefer uv-based runtime command.
5) Keep notes short and technical.
"""

_FILES_PROMPT_TEMPLATE = """You are a senior DevOps assistant.

Generate ONLY the Docker-related files needed to build and run this project.
Return JSON only, shaped by schema.

Project structure (format: {format}):
---
{project_structure}
---

Structured context:
{context_json}

Execution plan:
{plan_json}

Hard rules:
1) Use only output paths: Dockerfile, */Dockerfile, docker-compose.yaml, docker-compose.yml.
2) All COPY/ADD sources in Dockerfiles must exist in context.paths.
3) Never include `version:` in docker-compose.
4) If Dockerfile uses `uv sync`, runtime command must use `uv run ...` OR explicit `.venv/bin/...` binary.
5) Respect runtime constraints from manifests (for example requires-python vs base image tag).
6) If plan or context indicates FastAPI factory usage, run uvicorn with --factory.
7) Escape newlines correctly in JSON strings.
"""

_REPAIR_PROMPT_TEMPLATE = """Fix the previous response so that it satisfies all constraints.
Return only JSON by schema: {{"files": [{{"path": "...", "content": "..."}}, ...]}}

Original file-generation prompt:
---
{original_prompt}
---

Validation errors to fix:
{errors}

Previous model output:
---
{previous_output}
---
"""


@dataclass(slots=True)
class ValidationOutcome:
    files: list[FileContent]
    errors: list[str]


def _extract_json(text: str) -> dict[str, Any]:
    payload = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", payload)
    if match:
        payload = match.group(1).strip()
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("Model output is not a JSON object")
    return data


def _call_gemini_json(
    client: genai.Client,
    prompt: str,
    response_schema: dict[str, Any],
    temperature: float = 0.1,
) -> dict[str, Any]:
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "temperature": temperature,
            "response_mime_type": "application/json",
            "response_json_schema": response_schema,
        },
    )
    raw = response.text
    if not raw:
        raise ValueError("Gemini returned empty response")
    return _extract_json(raw)


def _context_to_json(project_context: ProjectContext | None) -> str:
    if project_context is None:
        return json.dumps(
            {"paths": [], "manifests": {}, "entrypoints": [], "commands": []},
            ensure_ascii=False,
            indent=2,
        )
    return project_context.model_dump_json(indent=2, exclude_none=True)


def _parse_files(data: dict[str, Any]) -> list[FileContent]:
    files = data.get("files")
    if not isinstance(files, list):
        raise ValueError("Gemini response missing 'files' array")
    parsed: list[FileContent] = []
    for item in files:
        if isinstance(item, dict) and isinstance(item.get("path"), str) and isinstance(item.get("content"), str):
            parsed.append(FileContent(path=item["path"], content=item["content"]))
    return parsed


def _has_factory_signal(project_context: ProjectContext | None, plan: dict[str, Any] | None = None) -> bool:
    if project_context and any("--factory" in cmd for cmd in project_context.commands):
        return True
    if project_context and any("main.py" in ep for ep in project_context.entrypoints):
        return True
    if isinstance(plan, dict):
        for service in plan.get("services", []):
            if isinstance(service, dict) and "--factory" in str(service.get("runtime_command", "")):
                return True
    return False


def _validate(
    files: list[FileContent],
    project_context: ProjectContext | None,
    plan: dict[str, Any] | None = None,
) -> ValidationOutcome:
    errors: list[str] = []
    project_paths = set(project_context.paths) if project_context else set()
    expect_factory = _has_factory_signal(project_context, plan)
    min_python = _extract_min_python(project_context.manifests if project_context else {})
    for file in files:
        path = file.path.strip()
        if not _is_allowed_output_path(path):
            errors.append(f"Unsupported output path: {path}")
            continue
        lower_path = path.lower()
        content = file.content
        if lower_path in {"docker-compose.yaml", "docker-compose.yml"} and re.search(r"(?im)^\s*version\s*:", content):
            errors.append(f"{path}: remove obsolete 'version' from compose file")
        if path == "Dockerfile" or path.endswith("/Dockerfile"):
            if "uv sync" in content and not _has_uv_runtime(content):
                errors.append(f"{path}: uses 'uv sync' but runtime command is not 'uv run ...' or '.venv/bin/...'")
            if expect_factory and "uvicorn" in content and "--factory" not in content:
                errors.append(f"{path}: expected FastAPI factory run with '--factory'")
            if min_python is not None:
                base = _extract_python_base_version(content)
                if base is not None and base < min_python:
                    errors.append(
                        f"{path}: python base image {base[0]}.{base[1]} is lower than requires-python >= {min_python[0]}.{min_python[1]}"
                    )
            if project_paths:
                errors.extend(_validate_copy_sources(path, content, project_paths))
    if not files:
        errors.append("Model returned empty files list")
    return ValidationOutcome(files=files, errors=errors)


def _is_allowed_output_path(path: str) -> bool:
    if not path or path.startswith("/") or ".." in path.split("/"):
        return False
    if path in {"Dockerfile", "docker-compose.yaml", "docker-compose.yml"}:
        return True
    return path.endswith("/Dockerfile")


def _has_uv_runtime(content: str) -> bool:
    return bool(re.search(r"\buv\s+run\b", content) or ".venv/bin/" in content)


def _extract_min_python(manifests: dict[str, str]) -> tuple[int, int] | None:
    pyproject = ""
    for key, value in manifests.items():
        if key.endswith("pyproject.toml"):
            pyproject = value
            break
    if not pyproject:
        return None
    match = re.search(r'requires-python\s*=\s*["\']([^"\']+)["\']', pyproject)
    if not match:
        return None
    spec = match.group(1)
    floor = re.search(r">=\s*(\d+)\.(\d+)", spec)
    if not floor:
        return None
    return int(floor.group(1)), int(floor.group(2))


def _extract_python_base_version(dockerfile: str) -> tuple[int, int] | None:
    for line in dockerfile.splitlines():
        match = re.search(r"(?i)^\s*FROM\s+python:(\d+)\.(\d+)", line)
        if match:
            return int(match.group(1)), int(match.group(2))
    return None


def _validate_copy_sources(path: str, dockerfile: str, project_paths: set[str]) -> list[str]:
    errors: list[str] = []
    for line in dockerfile.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        instruction = re.match(r"(?i)^(COPY|ADD)\s+(.+)$", stripped)
        if not instruction:
            continue
        _, args = instruction.groups()
        sources = _parse_copy_sources(args)
        for source in sources:
            normalized = source.lstrip("./")
            if not normalized or normalized in {".", "/"}:
                continue
            if "://" in normalized or normalized.startswith("$"):
                continue
            if any(ch in normalized for ch in ("*", "?", "[")):
                continue
            if normalized in project_paths:
                continue
            dir_prefix = normalized.rstrip("/") + "/"
            if any(p.startswith(dir_prefix) for p in project_paths):
                continue
            errors.append(f"{path}: COPY/ADD source '{source}' not found in project context")
    return errors


def _parse_copy_sources(args: str) -> list[str]:
    payload = args.strip()
    if not payload:
        return []
    if payload.startswith("["):
        try:
            parsed = json.loads(payload)
            if isinstance(parsed, list) and len(parsed) > 1 and all(isinstance(x, str) for x in parsed):
                return parsed[:-1]
        except json.JSONDecodeError:
            return []
        return []
    try:
        parts = shlex.split(payload)
    except ValueError:
        return []
    filtered = [part for part in parts if not part.startswith("--")]
    if len(filtered) <= 1:
        return []
    return filtered[:-1]


def _build_repair_prompt(original_prompt: str, previous_output: str, errors: list[str]) -> str:
    error_lines = "\n".join(f"- {err}" for err in errors)
    return _REPAIR_PROMPT_TEMPLATE.format(
        original_prompt=original_prompt,
        errors=error_lines,
        previous_output=previous_output,
    )


def _generate_plan(
    client: genai.Client,
    project_structure: str,
    format: str,
    context_json: str,
) -> dict[str, Any]:
    prompt = _PLAN_PROMPT_TEMPLATE.format(
        format=format,
        project_structure=project_structure,
        context_json=context_json,
    )
    return _call_gemini_json(
        client=client,
        prompt=prompt,
        response_schema=PLAN_SCHEMA,
        temperature=0.1,
    )


def _is_valid_plan(data: dict[str, Any]) -> bool:
    services = data.get("services")
    return isinstance(services, list) and all(isinstance(item, dict) for item in services)


def generate_docker_files(
    project_structure: str,
    format: str,
    project_context: ProjectContext | None = None,
) -> list[FileContent]:
    if not s.gemini_api_key or s.gemini_api_key == "GEMINI_API_KEY":
        raise HTTPException(
            status_code=503,
            detail="Gemini API key is not configured",
        )

    client = genai.Client(api_key=s.gemini_api_key)
    context_json = _context_to_json(project_context)

    try:
        plan = _generate_plan(
            client=client,
            project_structure=project_structure,
            format=format,
            context_json=context_json,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini plan generation failed: {exc!s}",
        ) from exc

    if not _is_valid_plan(plan):
        raise HTTPException(
            status_code=502,
            detail="Gemini returned invalid plan structure",
        )

    plan_json = json.dumps(plan, ensure_ascii=False, indent=2)
    base_prompt = _FILES_PROMPT_TEMPLATE.format(
        format=format,
        project_structure=project_structure,
        context_json=context_json,
        plan_json=plan_json,
    )
    prompt = base_prompt
    errors: list[str] = []

    for _ in range(MAX_ATTEMPTS):
        try:
            data = _call_gemini_json(
                client=client,
                prompt=prompt,
                response_schema=FILES_SCHEMA,
                temperature=0.1,
            )
            files = _parse_files(data)
        except Exception as exc:
            errors = [f"Response parse error: {exc!s}"]
            prompt = _build_repair_prompt(base_prompt, "{}", errors)
            continue

        outcome = _validate(files, project_context, plan=plan)
        if not outcome.errors:
            return outcome.files

        errors = outcome.errors
        prompt = _build_repair_prompt(
            base_prompt,
            json.dumps(data, ensure_ascii=False, indent=2),
            errors,
        )

    raise HTTPException(
        status_code=502,
        detail=f"Gemini produced invalid docker config after {MAX_ATTEMPTS} attempts: {'; '.join(errors)}",
    )
