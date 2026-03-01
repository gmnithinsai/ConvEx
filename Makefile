.PHONY: debug frontend backend ui

debug:
	adk web src/agents

frontend:
	python -m http.server 5173 --directory frontend

ui: frontend

backend:
	uvicorn src.api.app:app --reload --host localhost --port 8000
