from pydantic import BaseModel, Field


class SummarizationOutput(BaseModel):
    summary: str = Field(description="Concise summary of the conversation.")
    key_points: list[str] = Field(
        description="Important facts or decisions captured from the conversation.",
    )
    open_items: list[str] = Field(
        description="Outstanding questions, missing information, or next steps.",
    )
