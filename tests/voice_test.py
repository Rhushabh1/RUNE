import asyncio

from app.ollama_agent import stream_ask_agent
from app.speech import SpeechOutput


async def main():
	print("\nRUNE LLM at your service!")
	speaker = SpeechOutput()

	# endless conversation loop with RUNE
	while True:
		question = input("\nYou: ").strip()
		# exit failsafe
		if question.lower() in ["exit", "quit"]:
			break
		if not question:
			continue
			
		response = await stream_ask_agent(question)
		# print(f"\nRUNE: {response}")
		
		# keeping speech playback on the main thread
		speaker.speak(response)


if __name__ == "__main__":
	asyncio.run(main())