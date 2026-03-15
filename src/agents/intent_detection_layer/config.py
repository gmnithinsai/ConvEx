from google.genai import types

from src.common.conversation_history import ConversationHistoryService
from src.configs.domain.domain_loader import (
    render_yaml,
)
from src.configs.domain.schema import IntentDetectionConfig
from src.configs.prompts.prompt_loader import render_prompt


# ----------------------------------------
# Static Instruction Builder
# ----------------------------------------
def build_intent_detection_static():
    """Returns rendered static instruction prompt."""
    return types.Content(
        role="user",
        parts=[
            types.Part(
                text=render_prompt(
                    "intent_detection_layer/intent_detection_static.jinja2",
                ),
            ),
        ],
    )


# ----------------------------------------
# Dynamic Instruction Builder
# ----------------------------------------
def build_intent_detection_instruction(context):
    """Returns rendered variable instruction prompt."""
    # Build conversation history
    conversation_history = ConversationHistoryService(context).build_history()

    # Load intents configuration
    intent_cfg = render_yaml(
        "domain/intents.yaml",
        schema=IntentDetectionConfig,
    )

    if not intent_cfg or not intent_cfg.intent_detection:
        raise ValueError("Intent detection config missing in intents.yaml")

    intent_config_dict = intent_cfg.intent_detection.model_dump()

    # Render prompt
    return render_prompt(
        "intent_detection_layer/intent_detection_variable.jinja2",
        conversation_history=conversation_history,
        context=context,
        **intent_config_dict,
    )
