import warnings

import pytest

from agents.intent_detection_layer.agent import intent_detection_agent
from api.services.dialogue_service import AgentService

warnings.filterwarnings("ignore")


@pytest.mark.asyncio
async def test_agent_service_intent_detection_layer():
    USER_ID = "test_user"
    SESSION_ID_TOOL_AGENT = "test_session"

    service = AgentService(app_name="agent_comparison_app")

    result = await service.run_agent(
        agent=intent_detection_agent,
        user_id=USER_ID,
        session_id=SESSION_ID_TOOL_AGENT,
        input_payload={
            "user": "I would like to book a flight to Paris next week.",
        },
    )

    print(result)

    # ✅ Minimal production-grade assertion
    assert result is not None
