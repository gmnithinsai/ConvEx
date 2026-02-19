import dotenv

from agents.root_agent.agent import conversation_pipeline_agent
from src.api.services.dialogue_service import AgentService

dotenv.load_dotenv()
import asyncio

root_agent = conversation_pipeline_agent


async def chat_box(USER_ID: str, SESSION_ID_TOOL_AGENT: str):
    service = AgentService(app_name="agent_comparison_app")

    initial_question = """question: Hello there! Let me know how could I assist you today? Please mention about the service you are looking for.
"""

    print("🤖 Agent is ready!")
    print("📌 Requirements:")
    print(initial_question)
    print("\nType 'bye', 'exit', or 'quit' to end the chat.\n")
    current_question = initial_question

    while True:
        customer_message = input("👤 You: ").strip()

        if customer_message.lower() in {"bye", "exit", "quit"}:
            print("👋 Conversation ended. Have a nice day!")
            break

        result = await service.run_agent(
            agent=conversation_pipeline_agent,
            user_id=USER_ID,
            session_id=SESSION_ID_TOOL_AGENT,
            input_payload={
                "customer_message": customer_message,
                "current_question": current_question,
            },
        )
        current_question = result.get("next_question", "No question provided.")

        print("🤖 Agent:", result.get("next_question"))


if __name__ == "__main__":
    asyncio.run(
        chat_box(
            USER_ID="test_user",
            SESSION_ID_TOOL_AGENT="test_session",
        ),
    )
