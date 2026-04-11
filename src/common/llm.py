import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google.adk.models import LlmRequest, LlmResponse
from google.adk.models.google_llm import Gemini
from google.adk.models.lite_llm import LiteLlm

# from google.adk.models import LlmRequest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class CustomGemini(Gemini):
    """Thin wrapper to match CustomLiteLlm interface."""

    async def generate_async(
        self,
        llm_request: LlmRequest,
        stream: bool = False,
    ) -> AsyncGenerator[LlmResponse]:
        async for response in self.generate_content_async(
            llm_request=llm_request,
            stream=stream,
        ):
            yield response


class CustomLiteLlm(LiteLlm):
    """
    Custom LiteLLM wrapper extending Google ADK LiteLlm.

    Relies on ADK's default LiteLLMClient.
    """

    def __init__(
        self,
        model: str,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ):
        # Pass everything to LiteLlm; ADK creates the client internally
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )

    async def generate_async(
        self,
        llm_request: LlmRequest,
        stream: bool = False,
    ) -> AsyncGenerator[LlmResponse]:
        """Thin async wrapper around LiteLlm.generate_content_async."""
        async for response in self.generate_content_async(
            llm_request=llm_request,
            stream=stream,
        ):
            yield response


def get_llm():
    google_api_key = os.getenv("GOOGLE_API_KEY")
    ollama_model = os.getenv("OLLAMA_MODEL")
    ollama_base_url = os.getenv("OLLAMA_API_BASE") or os.getenv("LLM_API_BASE")

    # ✅ OLLAMA_MODEL present: use LiteLlm with ollama_chat/gemma3:latest
    # ✅ OLLAMA_MODEL present: use LiteLlm with model and base_url from env
    if ollama_model:
        return CustomLiteLlm(model=ollama_model, base_url=ollama_base_url)
    # if ollama_model:
    #     return LiteLlm(model=ollama_model, base_url=ollama_base_url)

    # ✅ Native Gemini (wrapped)
    if google_api_key:
        MODEL_GEMINI_PRO = "gemini-3-flash-preview"
        return MODEL_GEMINI_PRO
        # return CustomGemini(
        #     model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
        #     api_key=google_api_key,
        # )

    # ✅ LiteLLM fallback
    return CustomLiteLlm(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_API_BASE"),
    )
