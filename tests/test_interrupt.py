import threading
import time

from app.tts import SpeechEngine


def main():
	speaker = SpeechEngine()
	speaker.reset_interrupt()
	text = "Tis is a long speech interruption test. I will continue speaking for several seconds. you hsould be able to stop me before i finish. This is another setence to make the test longer. I hope that you stop me from speaking now atleast. Oh god! Atleast now you get the sense that I will continue speaking. Please I beg you to stop this madness and end my misery once and for all."

	playback = threading.Thread(target = speaker.speak, args = (text,))
	playback.start()

	input("\nPress Enter to interrupt playback")

	print("[TEST] Interrupting...")
	speaker.interrupt()

	# thread joins back
	playback.join()
	print("[TEST] Playback stopped")


if __name__ == "__main__":
	main()