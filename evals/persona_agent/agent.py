from google.adk.agents import LlmAgent

from evals.persona_agent.config import (
    build_persona_instruction,
    build_persona_static_instruction,
)
from evals.persona_agent.schema import PersonaAgentInput
from src.common.llm import get_llm

persona_agent = LlmAgent(
    model=get_llm(),
    name="persona_agent",
    description="Replies as a selected persona to the root-agent question.",
    static_instruction=build_persona_static_instruction(),
    instruction=build_persona_instruction,
    input_schema=PersonaAgentInput,
    output_key="persona_agent_output",
)


__all__ = ["persona_agent"]
