import asyncio

# from app.agent import ask_agent
from app.ollama_agent import stream_ask_agent, ask_agent


# async def main():
# 	print("\nRUNE LLM at your service!")

# 	# endless conversation loop with RUNE
# 	while True:
# 		question = input("\nYou: ").strip()
# 		# exit failsafe
# 		if question.lower() in ["exit", "quit"]:
# 			break
# 		if not question:
# 			continue
			
# 		response = await ask_agent(question)
# 		print(f"\nRUNE: {response}")


async def main_ollama():
	print("\nRUNE (OLLAMA) at your service!")

	# endless conversation loop with RUNE
	while True:
		question = input("\nYou: ").strip()
		# exit failsafe
		if question.lower() in ["exit", "quit"]:
			break
		if not question:
			continue
			
		response = await stream_ask_agent(question)
		# already printed by the agent
		# print(f"\nRUNE: {response}")


if __name__ == "__main__":
	asyncio.run(main_ollama())