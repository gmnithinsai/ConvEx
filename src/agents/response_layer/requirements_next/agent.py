from google.adk.agents import LlmAgent

from src.agents.response_layer.requirements_next.config import (
    requirements_next_instruction,
    requirements_next_static_instruction,
)
from src.agents.response_layer.requirements_next.schema import (
    RequirementsNextInput,
    RequirementsNextOutput,
)
from src.common.llm import get_llm
from src.common.requirement_updater import update_attempt_count_from_next_output

requirement_next_agent = LlmAgent(
    model=get_llm(),
    name="requirements_next_agent",
    description="Determines the next requirement to ask.",
    static_instruction=requirements_next_static_instruction(),
    instruction=requirements_next_instruction,
    input_schema=RequirementsNextInput,
    output_key="requirements_next_output",
    output_schema=RequirementsNextOutput,
    after_agent_callback=update_attempt_count_from_next_output,
)


__all__ = ["requirement_next_agent"]
