from google.adk.agents import LlmAgent

from src.agents.response_layer.information_extraction.config import (
    build_information_extraction_instruction,
    build_information_extraction_static_instruction,
)
from src.agents.response_layer.information_extraction.schema import (
    InformationExtractionInput,
    InformationExtractionOutput,
)
from src.common.llm import get_llm

information_extraction_agent = LlmAgent(
    model=get_llm(),
    name="information_extraction_agent",
    description="Identifies the information in the customer response.",
    static_instruction=build_information_extraction_static_instruction(),
    instruction=build_information_extraction_instruction,
    input_schema=InformationExtractionInput,
    output_key="information_extraction_output",
    output_schema=InformationExtractionOutput,
)
