from google.adk.agents import SequentialAgent

from src.agents.intent_detection_layer.agent import intent_detection_agent
from src.agents.response_layer.information_extraction.agent import (
    information_extraction_agent,
)
from src.agents.response_layer.requirements_next.agent import requirement_next_agent

conversation_pipeline_agent = SequentialAgent(
    name="conversation_pipeline_agent",
    sub_agents=[
        intent_detection_agent,
        information_extraction_agent,
        requirement_next_agent,
    ],
    description="Executes a sequence of intent detection, information extraction, and requirements next agents.",
    # The agents will run in the order provided: Intent Detection -> Information Extraction -> Requirements Next
)

root_agent = conversation_pipeline_agent


__all__ = ["conversation_pipeline_agent"]
