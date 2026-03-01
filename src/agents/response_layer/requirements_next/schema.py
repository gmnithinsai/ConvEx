from typing import Literal, List, Optional

from pydantic import BaseModel, Field


class QuestionStatus(BaseModel):
    id: str = Field(..., description="Unique identifier of the question")

    status: Literal["satisfied", "not_satisfied"] = Field(
        ...,
        description="Whether the requirement question is satisfied or not",
    )

    explanation: str = Field(
        ...,
        description="Explanation for the status, especially required if not satisfied",
    )


class RequirementStatus(BaseModel):
    title: str = Field(..., description="Requirement title")

    questions: list[QuestionStatus] = Field(
        ...,
        description="List of questions under this requirement",
    )


class RequirementsNextOutput(BaseModel):
    satisfied_fields: List[str] = Field(
        ...,
        description="List of field IDs satisfied in the latest message (excluding the current question)."
    )
    next_question: str = Field(
        ...,
        description="The exact next question string, a re-ask message, or a completion message."
    )
    next_question_id: Optional[str] = Field(
        ...,
        description="ID of the next question. Use current question ID if re-asking. Use None if flow is complete."
    )
    logic_applied: str = Field(
        ...,
        description="Brief internal note explaining why the flow moved forward or re-asked."
    )
class RequirementsNextInput(BaseModel):
    customer_message: str = Field(description="The message from the customer.")
    current_question: str = Field(
        description="The current question being asked to the customer."
    )
