from google.adk.agents import LlmAgent

from src.agents.intent_detection_layer.config import (
    build_intent_detection_instruction,
    build_intent_detection_static,
)
from src.agents.intent_detection_layer.schema import (
    IntentDetectionInput,
    IntentDetectionOutput,
)
from src.common.llm import get_llm

intent_detection_agent = LlmAgent(
    model=get_llm(),
    name="intent_detection_agent",
    description="Identifies the intent of the customer response.",
    static_instruction=build_intent_detection_static(),
    instruction=build_intent_detection_instruction,
    input_schema=IntentDetectionInput,
    output_key="intent_detection_agent_output",
    output_schema=IntentDetectionOutput,
)


__all__ = ["intent_detection_agent"]
