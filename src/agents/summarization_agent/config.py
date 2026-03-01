from google.genai import types

from src.common.conversation_history import ConversationHistoryService
from src.configs.prompts.prompt_loader import render_prompt


def build_summarization_static_instruction() -> types.Content:
    return types.Content(
        role="user",
        parts=[
            types.Part(
                text=render_prompt(
                    "summarization_agent/summarization_static.jinja2",
                ),
            ),
        ],
    )


def build_summarization_instruction(context):
    conversation_history = context.session.state.get("conversation_history")

    if not conversation_history:
        conversation_history = ConversationHistoryService(context).build_history()

    return render_prompt(
        "summarization_agent/summarization_variable.jinja2",
        conversation_history=conversation_history,
        context=context,
    )
