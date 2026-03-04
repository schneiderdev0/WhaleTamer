import json
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from google import genai
from google.genai import errors as genai_errors
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import s
from app.modules.collector.models import CollectorEvent

GEMINI_MODEL = "gemini-2.5-flash"

REPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "issues": {"type": "array", "items": {"type": "string"}},
        "recommendations": {"type": "array", "items": {"type": "string"}},
        "observations": {"type": "object"},
    },
    "required": ["summary", "issues", "recommendations", "observations"],
}


class GeminiAuthError(Exception):
    pass


def _extract_json(text: str) -> dict[str, Any]:
    payload = text.strip()
    if payload.startswith("```"):
        payload = payload.strip("`").strip()
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("Gemini output is not a JSON object")
    return data


def _format_gemini_auth_error(exc: genai_errors.ClientError) -> str:
    raw = str(exc)
    if "reported as leaked" in raw:
        return "Gemini auth error: API key is reported as leaked. Generate a new key and update backend/.env."
    if "PERMISSION_DENIED" in raw:
        return "Gemini auth error: PERMISSION_DENIED. Verify API key and Gemini API access."
    return f"Gemini auth error: {raw}"


def _call_gemini_report(client: genai.Client, prompt: str) -> tuple[dict[str, Any], str | None]:
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "temperature": 0.2,
                "response_mime_type": "application/json",
                "response_json_schema": REPORT_SCHEMA,
            },
        )
    except genai_errors.ClientError as exc:
        if exc.code in {401, 403}:
            raise GeminiAuthError(_format_gemini_auth_error(exc)) from exc
        raise
    raw_text = response.text
    if not raw_text:
        raise ValueError("Gemini returned empty response")
    return _extract_json(raw_text), raw_text


async def generate_report_for_event(
    db: AsyncSession,
    user_id: UUID,
    event_id: UUID,
) -> tuple[dict[str, Any], str | None, str]:
    if not s.gemini_api_key or s.gemini_api_key == "GEMINI_API_KEY":
        raise HTTPException(status_code=503, detail="Gemini API key is not configured")

    stmt = select(CollectorEvent).where(CollectorEvent.id == event_id, CollectorEvent.user_id == user_id)
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collector event not found")

    prompt = (
        "You are an SRE assistant. Analyze server metrics/logs and produce a concise report.\n"
        "Return JSON only, shaped by schema.\n\n"
        f"Event source: {event.source}\n"
        f"Event payload:\n{json.dumps(event.payload, ensure_ascii=False, indent=2)}\n"
    )

    client = genai.Client(api_key=s.gemini_api_key)
    try:
        data, raw = _call_gemini_report(client, prompt)
    except GeminiAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini report generation failed: {exc!s}") from exc

    return data, raw, GEMINI_MODEL

