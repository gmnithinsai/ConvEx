from google.adk.agents import LlmAgent
from google.genai import types

from src.agents.intent_detection_layer.schema import IntentDetectionInput
from src.common.conversation_history import ConversationHistoryService
from src.common.llm import get_llm
from src.configs.domain.domain_loader import render_yaml
from src.configs.domain.schema import IntentDetectionConfig
from src.configs.prompts.prompt_loader import render_prompt

intent_detection_agent = LlmAgent(
    model=get_llm(),
    name="intent_detection_agent",
    description="Identifies the intent of the customer response.",
    static_instruction=types.Content(
        role="user",
        parts=[
            types.Part(
                text=render_prompt(
                    "intent_detection_layer/intent_detection_static.jinja2",
                ),
            ),
        ],
    ),
    instruction=lambda context: render_prompt(
        "intent_detection_layer/intent_detection_variable.jinja2",
        conversation_history=ConversationHistoryService(context).build_history(),
        context=context,
        **(
            render_yaml(
                "domain/intents.yaml",
                schema=IntentDetectionConfig,
            )
        ).intent_detection.model_dump(),
    ),
    input_schema=IntentDetectionInput,
    output_key="intent_detection_agent_output",
    # output_schema=IntentDetectionOutput,
)


__all__ = ["intent_detection_agent"]
