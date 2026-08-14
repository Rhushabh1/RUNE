from app.voice_activity import record_utterance


def main():
	print("VAD test starting...")

	audio = record_utterance()

	if len(audio) == 0:
		print("No speech was captured")
		return

	duration = len(audio) / 16000

	print("Recording successful")
	print(f"Samples: {len(audio)}")
	print(f"Duration: {duration} seconds")
	print(f"Audio range: {audio.min()} to {audio.max()}")


if __name__ == "__main__":
	main()