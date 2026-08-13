from app.speech import SpeechOutput


def main():
	speaker = SpeechOutput()

	for i in range(5):
		text = f"This is speech number {i+1}"
		print(text)
		speaker.speak(text)
		

if __name__ == "__main__":
	main()