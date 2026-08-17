from app.microphone import record_audio
from app.transcription import Transcriber


def main():
	transcriber = Transcriber()

	input("\nPress Enter when ready to record...")

	audio = record_audio(duration = 5)

	text = transcriber.transcribe(audio)

	print(f"Recognised speech: {text}")


if __name__ == "__main__":
	main()