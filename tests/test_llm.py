import pytest
from google.adk.models import LlmRequest

from common.llm import get_llm


@pytest.mark.asyncio
async def test_llm_generate_async():
    llm = get_llm()
    print("---------------------------------------")

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


import asyncio


def run_async_tests():
    asyncio.run(test_llm_generate_async())


if __name__ == "__main__":
    run_async_tests()
