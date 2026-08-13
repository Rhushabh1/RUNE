from app.microphone import record_audio
from app.transcription import SpeechInput


def main():
	speech_input = SpeechInput()

	input("\nPress Enter when ready to record...")

	audio = record_audio(duration = 5)

	text = speech_input.transcribe(audio)

	print(f"Recognised speech: {text}")


if __name__ == "__main__":
	main()