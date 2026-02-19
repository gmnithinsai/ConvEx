from pydantic import BaseModel, Field


class IntentDetectionInput(BaseModel):
    customer_message: str = Field(description="The message from the customer.")
    current_question: str = Field(
        description="The current question being asked to the customer."
    )


class IntentDetectionOutput(BaseModel):
    intent_selected: str = Field(
        description="The detected intent of the customer message."
    )
