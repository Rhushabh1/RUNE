import asyncio

from app.ollama_agent import ask_agent, agent


async def main():
	session = "test_tool"

	questions = [
				"what time is it right now?", 
				"what is today's date?",
				"search my knowledge base for Google",
				"explain what you found",
				]

	for question in questions:
		print(f"\nYou: {question}")

		answer = await ask_agent(question, session_id = session)

		print(f"\nRUNE: {answer}")

	agent.clear_session(session)


if __name__ == "__main__":
	asyncio.run(main())