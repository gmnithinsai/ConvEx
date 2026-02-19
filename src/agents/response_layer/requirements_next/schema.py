from typing import Literal

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
    requirements_status: list[RequirementStatus] = Field(
        ...,
        description="List of all requirement statuses",
    )

    next_question: str = Field(
        ...,
        description="Exact next question text or completion message",
    )

    next_question_id: str = Field(
        ...,
        description="Question ID for tracking the next question",
    )


class RequirementsNextInput(BaseModel):
    customer_message: str = Field(description="The message from the customer.")
    current_question: str = Field(
        description="The current question being asked to the customer."
    )
