from pydantic import BaseModel, Field


class InformationExtractionInput(BaseModel):
    customer_message: str = Field(description="The message from the customer.")
    current_question: str = Field(
        description="The current question being asked to the customer.",
    )


from typing import Literal

from pydantic import BaseModel, Field


class ExtractedData(BaseModel):
    question_id: str = Field(
        ...,
        description="ID of the active question being processed",
    )

    value: str | None = Field(
        None,
        description="Response extracted from customer input, or None if missing",
    )

    overall_status: Literal["COMPLETE", "MISSING_VARIABLES"] = Field(
        ...,
        description="Indicates whether extraction is complete or missing required variables",
    )

    explanation: str = Field(
        ...,
        description="Brief explanation about completeness, especially if variables are missing",
    )


class InformationExtractionOutput(BaseModel):
    extracted_data: ExtractedData
