import json
import re
from typing import Any, Dict

import requests

from app.config import settings
from app.services.ai_settings import normalize_model_name


class GeminiServiceError(Exception):
    """Raised when Gemini API fails or returns invalid output."""


class GeminiService:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def classify_thread(self, thread_payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt(thread_payload)
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            params={"key": self.api_key},
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                    "response_mime_type": "application/json",
                },
            },
            timeout=settings.gemini_timeout_seconds,
        )

        if not response.ok:
            raise GeminiServiceError(
                f"Gemini API error {response.status_code}: {response.text}"
            )

        data = response.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GeminiServiceError("Gemini API returned an unexpected response") from exc

        return self._extract_json(text)

    def _build_prompt(self, thread_payload: Dict[str, Any]) -> str:
        schema = {
            "model": self.model,
            "responses": [
                {
                    "response_id": "<string>",
                    "response_type": "confirmation|rejection|acknowledgment|request_info|unknown",
                    "confidence_score": 0.0,
                    "rationale": "<short rationale>",
                }
            ],
        }
        thread_json = json.dumps(thread_payload, ensure_ascii=True, indent=2)

        return (
            "You are classifying broker email responses to a data deletion request. "
            "Return ONLY a JSON object that matches this schema:\n"
            f"{json.dumps(schema, ensure_ascii=True, indent=2)}\n\n"
            "Rules:\n"
            "- Output must be valid JSON with no extra keys and no markdown.\n"
            "- Provide exactly one entry per input response_id.\n"
            "- Use response_type values only from the allowed list.\n"
            "- confidence_score must be a number between 0 and 1.\n"
            f"- Set model to \"{self.model}\".\n\n"
            "Response type definitions:\n"
            "- confirmation: broker confirms data deletion or removal.\n"
            "- rejection: broker denies the request or says no data found.\n"
            "- acknowledgment: broker received the request and is processing it.\n"
            "- request_info: broker requests more information or identity verification.\n"
            "- unknown: none of the above or unclear.\n\n"
            "Thread context (JSON):\n"
            f"{thread_json}\n"
        )

    def _extract_json(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise GeminiServiceError("Gemini output did not contain valid JSON")
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError as exc:
                raise GeminiServiceError("Gemini output contained invalid JSON") from exc


def list_gemini_models(api_key: str) -> list[str]:
    response = requests.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        params={"key": api_key},
        timeout=settings.gemini_timeout_seconds,
    )
    if not response.ok:
        raise GeminiServiceError(
            f"Gemini API error {response.status_code}: {response.text}"
        )

    data = response.json()
    models = []
    for item in data.get("models", []):
        methods = item.get("supportedGenerationMethods") or []
        if "generateContent" not in methods:
            continue
        name = item.get("name")
        if not name:
            continue
        models.append(normalize_model_name(name))

    return sorted(set(models))
