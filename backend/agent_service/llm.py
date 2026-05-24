from __future__ import annotations

import json
from functools import lru_cache
from typing import TypeVar

from pydantic import BaseModel

from .config import get_settings

T = TypeVar("T", bound=BaseModel)


class LLMUnavailable(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_chat_model():
    settings = get_settings()
    if not settings.llm_enabled:
        raise LLMUnavailable("OPENAI_API_KEY is not configured.")
    try:
        from langchain.chat_models import init_chat_model
    except Exception as exc:  # pragma: no cover - dependency guard
        raise LLMUnavailable(f"LangChain chat model dependencies are unavailable: {exc}") from exc
    return init_chat_model(settings.openai_model, temperature=0)


def invoke_structured(
    schema: type[T],
    *,
    system_prompt: str,
    user_payload: dict,
) -> T:
    """Invoke the configured LLM with a Pydantic structured output schema."""

    model = get_chat_model()
    structured_model = model.with_structured_output(schema)
    messages = [
        ("system", system_prompt),
        ("user", json.dumps(user_payload, ensure_ascii=False, indent=2)),
    ]
    return structured_model.invoke(messages)
