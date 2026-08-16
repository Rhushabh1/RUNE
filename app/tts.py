from pathlib import Path 
import numpy as np 
import sounddevice as sd 
from piper import PiperVoice


MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "en_US-lessac-medium.onnx"


# has streaming playback utility + true barge-in capability
class SpeechEngine():
	# voice model is loaded just once
	def __init__(self):
		if not MODEL_PATH.exists():
			raise FileNotFoundError(f"Piper model not found: {MODEL_PATH}")

		print("[TTS] Loading Piper voice...")
		self.voice = PiperVoice.load(str(MODEL_PATH))
		print("[TTS] Voice ready")


	# converts text into audio data (real TTS processing)
	def synthesize(self, text):
		audio_chunks = list(self.voice.synthesize(text))

		if not audio_chunks:
			return None, None 

		# combining all the byte-sized audio chunks together
		audio_bytes = b"".join(chunk.audio_int16_bytes for chunk in audio_chunks)
		# to play the audio sequence (frequency)
		sample_rate = audio_chunks[0].sample_rate

		audio = np.frombuffer(audio_bytes, dtype = np.int16).copy()

		return audio, sample_rate


	# handles user-facing audio playback
	def speak(self, text):
		if not text.strip():
			return

		audio, sample_rate = self.synthesize(text)

		if audio is None:
			return

		# actual playback happens
		sd.play(audio, 
				samplerate = sample_rate,
				# ensures one speech segment finishes before next begins (for now)
				blocking = True)
