import pytest
from google.adk.models import LlmRequest

from common.llm import get_llm


@pytest.mark.asyncio
async def test_llm_generate_async():
    llm = get_llm()

    request = LlmRequest(
        messages=[
            {"role": "user", "content": "Explain how ADK wraps LiteLLM"},
        ],
    )

    chunks = []

    async for resp in llm.generate_async(request):
        text = "".join(p.text for p in resp.content.parts if hasattr(p, "text"))
        chunks.append(text)

    full_output = "".join(chunks)

    # Production-grade assertion
    assert len(full_output) > 10
