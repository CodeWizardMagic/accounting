import json
import logging
from abc import ABC, abstractmethod

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    @abstractmethod
    async def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        raise NotImplementedError


class GroqProvider(AIProvider):
    endpoint = "https://api.groq.com/openai/v1/chat/completions"

    async def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")

        payload = {
            "model": settings.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        logger.info("Groq request model=%s prompt=%s", settings.groq_model, user_prompt)
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {settings.groq_api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        logger.info("Groq response=%s", content)
        return json.loads(content)


def get_ai_provider() -> AIProvider:
    if settings.ai_provider == "groq":
        return GroqProvider()
    raise ValueError(f"Unsupported AI provider: {settings.ai_provider}")
