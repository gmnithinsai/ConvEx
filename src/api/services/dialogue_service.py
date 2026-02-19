from __future__ import annotations

import json
import logging
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class AgentExecutionError(Exception):
    """Raised when agent execution fails."""


class AgentService:
    def __init__(
        self,
        app_name: str,
        session_service: InMemorySessionService | None = None,
    ) -> None:
        self.app_name = app_name
        self.session_service = session_service or InMemorySessionService()
        # Cache runners per agent name
        self._runner_cache: dict[str, Runner] = {}

    async def create_session(
        self,
        user_id: str,
        session_id: str,
    ) -> None:
        """Create a new session if it does not already exist."""
        try:
            await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id,
            )
            logger.info("Session created: %s", session_id)
        except Exception:
            # Session may already exist – safe to ignore
            logger.debug("Session already exists: %s", session_id)

    async def get_session_state(
        self,
        user_id: str,
        session_id: str,
    ) -> dict[str, Any]:
        """Retrieve session state (memory)."""
        session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id,
        )
        return session.state or {}

    def get_runner(self, agent: LlmAgent) -> Runner:
        """Lazily create and cache a Runner per agent."""
        if agent.name not in self._runner_cache:
            self._runner_cache[agent.name] = Runner(
                agent=agent,
                app_name=self.app_name,
                session_service=self.session_service,
            )
            logger.info("Runner created for agent: %s", agent.name)
        return self._runner_cache[agent.name]

    async def run_agent(
        self,
        agent: LlmAgent,
        *,
        user_id: str,
        session_id: str,
        input_payload: dict[str, Any],
    ) -> Any:
        await self.create_session(user_id, session_id)
        runner = self.get_runner(agent)

        user_message = types.Content(
            role="user",
            parts=[types.Part(text=json.dumps(input_payload))],
        )

        final_text: str | None = None
        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_message,
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_text = event.content.parts[0].text
        except Exception as exc:
            logger.exception("Agent execution failed")
            raise AgentExecutionError(str(exc)) from exc

        if final_text is None:
            raise AgentExecutionError("No final response received from agent")

        return self._parse_response(final_text)

    def _parse_response(self, response_text: str) -> Any:
        """Parse JSON responses if possible, otherwise return raw text."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return response_text

    async def get_agent_output_from_memory(
        self,
        agent: LlmAgent,
        *,
        user_id: str,
        session_id: str,
    ) -> Any:
        state = await self.get_session_state(user_id, session_id)
        return state.get(agent.output_key)
