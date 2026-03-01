from __future__ import annotations

from typing import Any
from pathlib import Path
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import yaml

from src.agents.root_agent.agent import conversation_pipeline_agent
from src.api.services.dialogue_service import AgentExecutionError, AgentService

router = APIRouter(prefix="/root-agent", tags=["root-agent"])
agent_service = AgentService(app_name="agent_comparison_app")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
INTENTS_PATH = PROJECT_ROOT / "src" / "configs" / "domain" / "intents.yaml"
PERSONA_CONFIG_PATH = PROJECT_ROOT / "evals" / "config" / "persona_config.yaml"
PERSONAS_DIR = PROJECT_ROOT / "evals" / "config" / "personas"


class RootAgentRunRequest(BaseModel):
    user_id: str = Field(description="Unique user identifier.")
    session_id: str = Field(description="Conversation session identifier.")
    customer_message: str = Field(description="Latest user message.")
    current_question: str = Field(
        default="Hello there! Let me know how could I assist you today?",
        description="Current question asked to the user.",
    )


class RootAgentRunResponse(BaseModel):
    result: Any = Field(description="Structured response returned by the root agent.")


class SessionStateResponse(BaseModel):
    state: dict[str, Any] = Field(description="Current state for the user session.")


class IntentsResponse(BaseModel):
    intents: list[str] = Field(description="Available configured intent names.")


class PersonaSummary(BaseModel):
    persona_id: str = Field(description="Unique persona id.")
    intent_name: str = Field(description="Intent associated with persona.")
    name: str = Field(description="Persona name.")
    email: str = Field(description="Persona email.")
    gender: str = Field(description="Persona gender.")
    nationality: str = Field(description="Persona nationality.")


class PersonasResponse(BaseModel):
    personas: list[PersonaSummary] = Field(description="Available personas for selected intent.")


@router.post("/run", response_model=RootAgentRunResponse)
async def run_root_agent(payload: RootAgentRunRequest) -> RootAgentRunResponse:
    try:
        result = await agent_service.run_agent(
            agent=conversation_pipeline_agent,
            user_id=payload.user_id,
            session_id=payload.session_id,
            input_payload={
                "customer_message": payload.customer_message,
                "current_question": payload.current_question,
            },
        )
    except AgentExecutionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return RootAgentRunResponse(result=result)


@router.get("/session-state", response_model=SessionStateResponse)
async def get_session_state(user_id: str, session_id: str) -> SessionStateResponse:
    state = await agent_service.get_session_state(
        user_id=user_id,
        session_id=session_id,
    )
    return SessionStateResponse(state=state)


@router.get("/persona-intents", response_model=IntentsResponse)
async def get_persona_intents() -> IntentsResponse:
    try:
        raw = yaml.safe_load(PERSONA_CONFIG_PATH.read_text(encoding="utf-8")) or {}
        intent_distribution = (
            raw.get("persona_config", {})
            .get("segments", {})
            .get("intent_distribution", {})
        )
        intents: list[str] = []
        if isinstance(intent_distribution, dict):
            for key, value in intent_distribution.items():
                if not str(key).endswith("_intent"):
                    continue
                value_list = value.get("values", []) if isinstance(value, dict) else []
                if isinstance(value_list, list):
                    intents.extend(str(item) for item in value_list)

        # Preserve order while removing duplicates.
        deduped_intents = list(dict.fromkeys(intents))
        return IntentsResponse(intents=deduped_intents)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to load persona intents: {exc}"
        ) from exc


@router.get("/intents", response_model=IntentsResponse)
async def get_intents() -> IntentsResponse:
    try:
        raw = yaml.safe_load(INTENTS_PATH.read_text(encoding="utf-8")) or {}
        intents = raw.get("intent_detection", {}).get("intents", [])
        if not isinstance(intents, list):
            intents = []
        return IntentsResponse(intents=[str(item) for item in intents])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load intents: {exc}") from exc


@router.get("/personas", response_model=PersonasResponse)
async def get_personas(intent_name: str) -> PersonasResponse:
    try:
        normalized_intent = intent_name.strip().lower().replace(" ", "_")
        file_path = PERSONAS_DIR / f"persona_{normalized_intent}.json"
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Persona file not found for intent '{intent_name}'.",
            )

        payload = json.loads(file_path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            payload = []

        personas: list[PersonaSummary] = []
        for index, item in enumerate(payload):
            if not isinstance(item, dict):
                continue
            demographics = item.get("demographics", {})
            if not isinstance(demographics, dict):
                demographics = {}
            personas.append(
                PersonaSummary(
                    persona_id=str(item.get("persona_id") or f"{normalized_intent}_{index}"),
                    intent_name=str(item.get("primary_intent") or intent_name),
                    name=str(demographics.get("name") or "Unknown"),
                    email=str(demographics.get("email") or ""),
                    gender=str(demographics.get("gender") or "Unknown"),
                    nationality=str(demographics.get("nationality") or "Unknown"),
                )
            )
        return PersonasResponse(personas=personas)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load personas: {exc}") from exc
