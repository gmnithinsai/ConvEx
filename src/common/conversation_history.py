import json
from typing import Any


class ConversationHistoryService:
    def __init__(self, context):
        """
        context.session.events is expected
        """
        self.events = getattr(context.session, "events", [])

    def build_history(self) -> list[dict[str, Any]]:
        """
        Build conversation history using:
        - raw user text
        - only next_question JSON
        """
        history: list[dict[str, Any]] = []

        for event in self.events:
            payload = self._extract_json(event)
            if not payload:
                continue

            # ✅ If it's plain text → treat as user message
            if isinstance(payload, str):
                history.append(
                    {
                        "role": "user",
                        "content": payload,
                    },
                )

            # ✅ If it's JSON and contains next_question → add only that
            elif isinstance(payload, dict) and "next_question" in payload:
                history.append(
                    {
                        "role": "assistant",
                        "content": payload["next_question"],
                    },
                )

        return history

    @staticmethod
    def _extract_json(event) -> dict[str, Any] | None:
        """Safely extract JSON from event.content.parts[].text."""
        content = getattr(event, "content", None)

        print("===========")
        # print(content)

        if not content or not getattr(content, "parts", None):
            return None

        for part in content.parts:
            text = getattr(part, "text", None)
            if not text:
                continue

            text = text.strip()

            # Try parsing as JSON
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                # If not JSON, return raw text instead
                return text
        return None
