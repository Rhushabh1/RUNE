import asyncio

from app.agent import ask_agent
from app.transcription import SpeechInput
from app.speech import SpeechOutput
# from app.microphone import record_audio
from app.voice_activity import record_utterance


async def main():
	print("Initialising RUNE voice agent...")

	# initialise all models and audio engines only once
	speech_input = SpeechInput()
	speech_output = SpeechOutput()

	print("RUNE is ready")
	# endless conversation loop
	while True:
		command = input("\nPress Enter to speak or type 'q' to quit: ").strip().lower()

		if command == "q":
			print("Shutting down RUNE...")
			break

		# (1) capture audio
		# audio = record_audio(duration = 5)
		audio = record_utterance()
		if len(audio) == 0:
			continue

		# (2) convert STT
		question = speech_input.transcribe(audio)
		if not question:
			print("No speech detected -> Try again")
			continue
		print(f"\nYou: {question}")

		# (3) generate agent response
		try:
			answer = await ask_agent(question)
		except Exception as error:
			print(f"RUNE error: {error}")
			continue
		print(f"\nRUNE: {answer}")

		# (4) convert TTS
		speech_output.speak(answer)


if __name__ == "__main__":
	asyncio.run(main())