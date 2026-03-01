from google.adk.agents import LlmAgent

from src.agents.summarization_agent.config import (
    build_summarization_instruction,
    build_summarization_static_instruction,
)
from src.agents.summarization_agent.schema import (
    SummarizationOutput,
)
from src.common.llm import get_llm


summarization_agent = LlmAgent(
    model=get_llm(),
    name="summarization_agent",
    description="Summarizes conversation history into concise structured output.",
    static_instruction=build_summarization_static_instruction(),
    instruction=build_summarization_instruction,
    output_key="summarization_output",
    output_schema=SummarizationOutput,
)


__all__ = ["summarization_agent"]
