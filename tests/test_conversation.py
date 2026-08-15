import asyncio

from app.agent import ask_agent, agent


async def test_session_isolation():
	session_a = "user_a"
	session_b = "user_b"

	await ask_agent("My name is Alice", session_id = session_a)
	await ask_agent("My name is Bob", session_id = session_b)

	answer_a = await ask_agent("What is my name?", session_id = session_a)
	answer_b = await ask_agent("What is my name?", session_id = session_b)

	print("Session A: ", answer_a)
	print("Session B: ", answer_b)


async def main():
	session = "memory_test"

	questions = ["My name is Sonu. Remember that",
				"What is my name?",
				"What did i ask you to remember?"]

	for question in questions:
		print(f"\nYou: {question}")

		answer = await ask_agent(question, session_id = session)

		print(f"RUNE: {answer}")

	print("\nClearing conversation...")
	agent.clear_session(session)
	print("Session cleared")


if __name__ == "__main__":
	# asyncio.run(main())
	asyncio.run(test_session_isolation())