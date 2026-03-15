from typing import Literal

from pydantic import BaseModel, Field


class RequirementFieldStatus(BaseModel):
    status: Literal["satisfied", "missing"] = Field(
        description="Status of the requirement field based on the user message",
    )
    reason: str = Field(
        description="Brief explanation for why the field is satisfied or missing",
    )


class RequirementsStatusUpdateOutput(BaseModel):
    requirements_status: dict[str, RequirementFieldStatus] = Field(
        description="Mapping of field_id to its evaluation status",
    )
