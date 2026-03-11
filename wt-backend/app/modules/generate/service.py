import json
import logging
import re
import shlex
import time
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from google import genai
from google.genai import errors as genai_errors

from app.core.settings import s
from app.modules.generate.analyzer import analyze_project_context
from app.modules.generate.local_templates import generate_local_files
from app.modules.generate.schemas import FileContent, ProjectContext

GEMINI_MODEL = "gemini-2.5-flash"
MAX_ATTEMPTS = 3
MAX_QUOTA_RETRIES = 2
MAX_RETRY_DELAY_SECONDS = 45
LOG_SNIPPET_LIMIT = 600

logger = logging.getLogger(__name__)

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
8) Service environment variables must match project settings usage. If settings/database code uses postgres_host/postgres_user/postgres_password/postgres_db, then provide POSTGRES_* vars to app and migrations services (not only DATABASE_URL).
9) For Rust projects, never use deprecated Debian releases like buster and never install `libssl1.1`; prefer current images such as `rust:<version>-bookworm` and `debian:bookworm-slim` or another currently supported base image.
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


class GeminiAuthError(Exception):
    """Fatal Gemini auth/permission error. Must not be retried."""


class GeminiQuotaError(Exception):
    """Gemini quota/rate-limit error after retries."""


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
    stage: str = "files",
) -> dict[str, Any]:
    prompt_size = len(prompt)
    for attempt in range(MAX_QUOTA_RETRIES + 1):
        try:
            logger.info(
                "Gemini request started: stage=%s model=%s attempt=%s prompt_chars=%s",
                stage,
                GEMINI_MODEL,
                attempt + 1,
                prompt_size,
            )
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
                logger.warning(
                    "Gemini returned empty response: stage=%s model=%s attempt=%s",
                    stage,
                    GEMINI_MODEL,
                    attempt + 1,
                )
                raise ValueError("Gemini returned empty response")
            logger.info(
                "Gemini response received: stage=%s model=%s attempt=%s response_chars=%s snippet=%r",
                stage,
                GEMINI_MODEL,
                attempt + 1,
                len(raw),
                _clip_for_log(raw),
            )
            return _extract_json(raw)
        except genai_errors.ClientError as exc:
            logger.warning(
                "Gemini client error: stage=%s model=%s attempt=%s code=%s retry_delay=%s raw=%r",
                stage,
                GEMINI_MODEL,
                attempt + 1,
                getattr(exc, "code", None),
                _extract_retry_delay_seconds(exc),
                _clip_for_log(str(exc)),
            )
            if exc.code in {401, 403}:
                raise GeminiAuthError(_format_gemini_auth_error(exc)) from exc
            if exc.code == 429 or "RESOURCE_EXHAUSTED" in str(exc):
                delay = _extract_retry_delay_seconds(exc)
                if attempt < MAX_QUOTA_RETRIES and delay > 0:
                    logger.info(
                        "Gemini quota retry scheduled: stage=%s model=%s next_attempt=%s sleep_seconds=%s",
                        stage,
                        GEMINI_MODEL,
                        attempt + 2,
                        delay,
                    )
                    time.sleep(delay)
                    continue
                raise GeminiQuotaError(_format_gemini_quota_error(exc, delay)) from exc
            raise
        except Exception as exc:
            logger.exception(
                "Gemini unexpected error: stage=%s model=%s attempt=%s error=%r",
                stage,
                GEMINI_MODEL,
                attempt + 1,
                exc,
            )
            raise
    raise GeminiQuotaError("Gemini quota exceeded. Retry later.")


def _format_gemini_auth_error(exc: genai_errors.ClientError) -> str:
    raw = str(exc)
    if "reported as leaked" in raw:
        return "Gemini auth error: API key is reported as leaked. Generate a new key and update backend/.env."
    if "PERMISSION_DENIED" in raw:
        return "Gemini auth error: PERMISSION_DENIED. Verify API key and Gemini API access."
    return f"Gemini auth error: {raw}"


def _extract_retry_delay_seconds(exc: genai_errors.ClientError) -> int:
    raw = str(exc)
    match = re.search(r"retry in\s+(\d+(?:\.\d+)?)s", raw, flags=re.IGNORECASE)
    if not match:
        match = re.search(r"'retryDelay':\s*'(\d+)s'", raw)
    if not match:
        return 0
    try:
        value = int(float(match.group(1)))
    except ValueError:
        return 0
    return max(0, min(value + 1, MAX_RETRY_DELAY_SECONDS))


def _format_gemini_quota_error(exc: genai_errors.ClientError, delay: int) -> str:
    raw = str(exc)
    if delay > 0:
        return f"Gemini quota exceeded for {GEMINI_MODEL}. Automatic retry window expired; retry in about {delay} seconds."
    if "RESOURCE_EXHAUSTED" in raw or "quota" in raw.lower():
        return f"Gemini quota exceeded for {GEMINI_MODEL}. Retry later or increase Gemini API quota."
    return f"Gemini request failed: {raw}"


def _clip_for_log(value: str, limit: int = LOG_SNIPPET_LIMIT) -> str:
    cleaned = " ".join(value.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit] + "...[truncated]"


def _context_to_json(project_context: ProjectContext | None) -> str:
    if project_context is None:
        return json.dumps(
            {"paths": [], "manifests": {}, "entrypoints": [], "commands": []},
            ensure_ascii=False,
            indent=2,
        )
    return project_context.model_dump_json(indent=2, exclude_none=True)


def _log_generation_input(project_structure: str, project_context: ProjectContext | None, context_json: str) -> None:
    if project_context is None:
        logger.info(
            "Gemini input summary: project_structure_chars=%s context_json_chars=%s paths=0 manifests=0 manifests_chars=0 entrypoints=0 commands=0",
            len(project_structure),
            len(context_json),
        )
        return

    manifests = project_context.manifests or {}
    manifest_chars = sum(len(content) for content in manifests.values())
    logger.info(
        "Gemini input summary: project_structure_chars=%s context_json_chars=%s paths=%s manifests=%s manifests_chars=%s entrypoints=%s commands=%s",
        len(project_structure),
        len(context_json),
        len(project_context.paths or []),
        len(manifests),
        manifest_chars,
        len(project_context.entrypoints or []),
        len(project_context.commands or []),
    )
    if manifests:
        logger.info(
            "Gemini manifest summary: keys=%s",
            [key for key in sorted(manifests.keys())],
        )


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
    is_rust_project = _is_rust_project(project_context)
    for file in files:
        path = file.path.strip()
        if not _is_allowed_output_path(path):
            errors.append(f"Unsupported output path: {path}")
            continue
        lower_path = path.lower()
        content = file.content
        if lower_path in {"docker-compose.yaml", "docker-compose.yml"} and re.search(r"(?im)^\s*version\s*:", content):
            errors.append(f"{path}: remove obsolete 'version' from compose file")
        if lower_path in {"docker-compose.yaml", "docker-compose.yml"}:
            errors.extend(_validate_compose_env_contract(path, content, project_context))
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
            if is_rust_project:
                errors.extend(_validate_rust_dockerfile(path, content))
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


def _is_rust_project(project_context: ProjectContext | None) -> bool:
    if project_context is None:
        return False
    if any(path.endswith("Cargo.toml") for path in project_context.paths):
        return True
    return any(path.endswith("Cargo.toml") for path in project_context.manifests)


def _validate_rust_dockerfile(path: str, dockerfile: str) -> list[str]:
    errors: list[str] = []
    lowered = dockerfile.lower()
    if "debian:buster" in lowered or "buster-slim" in lowered or re.search(r"(?im)^\s*from\s+rust:.*buster", lowered):
        errors.append(f"{path}: Rust Dockerfile uses deprecated Debian buster base image")
    if "libssl1.1" in lowered:
        errors.append(f"{path}: Rust Dockerfile installs deprecated package libssl1.1")
    return errors


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


def _validate_compose_env_contract(
    path: str,
    compose_content: str,
    project_context: ProjectContext | None,
) -> list[str]:
    errors: list[str] = []
    if project_context is None:
        return errors
    if not _project_uses_postgres_settings(project_context):
        return errors

    has_database_url = bool(re.search(r"(?im)^\s*DATABASE_URL\s*:", compose_content))
    has_postgres_vars = all(
        re.search(rf"(?im)^\s*{name}\s*:", compose_content)
        for name in ("POSTGRES_HOST", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB")
    )
    if has_database_url and not has_postgres_vars:
        errors.append(
            f"{path}: project settings appear to use POSTGRES_* variables, but compose defines only DATABASE_URL"
        )
    return errors


def _project_uses_postgres_settings(project_context: ProjectContext) -> bool:
    snippets = project_context.snippets or {}
    merged = "\n".join(snippets.values())
    if not merged:
        return False
    return all(key in merged for key in ("postgres_host", "postgres_user", "postgres_password", "postgres_db"))


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
        stage="plan",
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
    _log_generation_input(project_structure=project_structure, project_context=project_context, context_json=context_json)
    analysis = analyze_project_context(project_context)
    logger.info("Local analyzer summary: %s", analysis.to_log_dict())
    local_files = generate_local_files(analysis, project_context)
    if local_files:
        logger.info("Local template generation selected: stack=%s files=%s", analysis.stack, [f.path for f in local_files])
        outcome = _validate(local_files, project_context, plan=None)
        if not outcome.errors:
            return outcome.files
        logger.warning("Local template validation failed, falling back to Gemini: errors=%s", outcome.errors)

    try:
        plan = _generate_plan(
            client=client,
            project_structure=project_structure,
            format=format,
            context_json=context_json,
        )
    except GeminiQuotaError as exc:
        raise HTTPException(
            status_code=429,
            detail=str(exc),
        ) from exc
    except GeminiAuthError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
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
                stage="files" if prompt == base_prompt else "repair",
            )
            files = _parse_files(data)
        except GeminiQuotaError as exc:
            raise HTTPException(
                status_code=429,
                detail=str(exc),
            ) from exc
        except GeminiAuthError as exc:
            raise HTTPException(
                status_code=502,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            errors = [f"Generation error: {exc!s}"]
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
