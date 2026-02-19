from pydantic import BaseModel, Field


class IntentDetectionSchema(BaseModel):
    fallback: str = Field(..., min_length=1)
    intents: list[str] = Field(..., min_items=1)


class IntentDetectionConfig(BaseModel):
    intent_detection: IntentDetectionSchema
