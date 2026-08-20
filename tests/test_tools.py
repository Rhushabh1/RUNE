import asyncio

from app.ollama_agent import ask_agent, agent


async def main():
	session = "test_tool"

	questions = [
				"My name is Rushab. Remember this.",
		        "I enjoy badminton, swimming, table tennis, chess and art. Save these interests.",
		        "I play badminton on wooden courts and I am a doubles badminton champion.",
		        "What have you saved about me?",
		        "Search your memories for my sports interests.",
		        "What is my badminton achievement?"
				]

	for question in questions:
		print(f"\nYou: {question}")

		answer = await ask_agent(question, session_id = session)

		print(f"\nRUNE: {answer}")

	agent.clear_session(session)


if __name__ == "__main__":
	asyncio.run(main())