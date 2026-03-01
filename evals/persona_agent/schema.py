from pydantic import BaseModel, Field


class PersonaAgentInput(BaseModel):
    prompt_text: str = Field(description="Fully rendered persona prompt.")

