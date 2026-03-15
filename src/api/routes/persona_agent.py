from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from evals.persona_agent.agent import persona_agent
from evals.persona_agent.config import render_persona_prompt
from src.api.services.dialogue_service import AgentExecutionError, AgentService

router = APIRouter(prefix="/persona-agent", tags=["persona-agent"])
agent_service = AgentService(app_name="persona_agent_app")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PERSONAS_DIR = PROJECT_ROOT / "evals" / "config" / "personas"


class PersonaAgentRunRequest(BaseModel):
    user_id: str = Field(description="Unique user identifier.")
    session_id: str = Field(description="Conversation session identifier.")
    persona_id: str = Field(description="Selected persona identifier.")
    intent_name: str = Field(description="Selected intent name.")
    user_question: str = Field(description="Question asked by the root agent.")


class PersonaAgentRunResponse(BaseModel):
    reply: str = Field(description="Persona reply text.")
    persona: dict[str, Any] = Field(description="Persona details used for generation.")


def _load_persona(intent_name: str, persona_id: str) -> dict[str, Any]:
    normalized_intent = intent_name.strip().lower().replace(" ", "_")
    file_path = PERSONAS_DIR / f"persona_{normalized_intent}.json"
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Persona file not found for intent '{intent_name}'.",
        )

    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise HTTPException(status_code=500, detail="Persona file format is invalid.")

    for item in payload:
        if isinstance(item, dict) and str(item.get("persona_id")) == persona_id:
            return item

    raise HTTPException(
        status_code=404,
        detail=f"Persona '{persona_id}' not found for intent '{intent_name}'.",
    )


def _render_persona_prompt(persona: dict[str, Any], user_question: str) -> str:
    try:
        return render_persona_prompt(persona=persona, user_question=user_question)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/run", response_model=PersonaAgentRunResponse)
async def run_persona_agent(payload: PersonaAgentRunRequest) -> PersonaAgentRunResponse:
    persona = _load_persona(payload.intent_name, payload.persona_id)
    prompt_text = _render_persona_prompt(
        persona=persona, user_question=payload.user_question
    )

    try:
        result = await agent_service.run_agent(
            agent=persona_agent,
            user_id=payload.user_id,
            session_id=payload.session_id,
            input_payload={"prompt_text": prompt_text},
        )
    except AgentExecutionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    reply = result if isinstance(result, str) else json.dumps(result)
    return PersonaAgentRunResponse(reply=reply, persona=persona)
