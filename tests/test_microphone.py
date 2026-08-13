import sounddevice as sd 

from app.microphone import record_audio


def main():
	print("Available audio devices: ")
	print(sd.query_devices())

	input("\nPress Enter when ready to record...")

	audio = record_audio(duration = 5)

	print(f"Recorded sample: {len(audio)}")
	print(f"Duration: {len(audio)/16000} seconds")


if __name__ == "__main__":
	main()