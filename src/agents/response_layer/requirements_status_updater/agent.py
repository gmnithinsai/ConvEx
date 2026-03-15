from google.adk.agents import LlmAgent

from src.agents.response_layer.requirements_status_updater.config import (
    requirements_status_updater_instruction,
    requirements_status_updater_static_instruction,
)
from src.agents.response_layer.requirements_status_updater.schema import (
    RequirementsStatusUpdateOutput,
)
from src.common.llm import get_llm
from src.common.requirement_updater import update_attempt_count_from_status_update

requirement_status_updater_agent = LlmAgent(
    model=get_llm(),
    name="requirements_status_updater_agent",
    description="Updates the status of requirements.",
    static_instruction=requirements_status_updater_static_instruction(),
    instruction=requirements_status_updater_instruction,
    output_key="requirements_status_update",
    output_schema=RequirementsStatusUpdateOutput,
    after_agent_callback=update_attempt_count_from_status_update,
)


__all__ = ["requirement_status_updater_agent"]
