from pathlib import Path 
import threading
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

		# true barge-in -> interrupting the audio stream
		# communicates that interruption has been requested
		self._interrupted = threading.Event()		# shared boolean flag
		# protects access to active audio stream (playback & interruption threads are concurrent)
		self._stream_lock = threading.Lock()
		self._active_stream = None
		
		print("[TTS] Voice ready")


	# allowing new response to be spoken 
	# not while old playback is still being interrupted -> may accidentally re-enable the old playback
	def reset_interrupt(self):
		self._interrupted.clear()


	# stops current audio stream
	def interrupt(self):
		self._interrupted.set()

		with self._stream_lock:
			stream = self._active_stream

		if stream is not None:
			try:
				# aborted even before it reaches next Event check
				stream.abort()
			except Exception:
				pass


	# to expose playback status (for interruption)
	@property
	def is_playing(self):
		with self._stream_lock:
			return self._active_stream is not None


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

		if self._interrupted.is_set():
			return

		audio, sample_rate = self.synthesize(text)

		if audio is None or self._interrupted.is_set():
			return

		# # full playback happens at once
		# sd.play(audio, 
		# 		samplerate = sample_rate,
		# 		# ensures one speech segment finishes before next begins (for now)
		# 		blocking = True)

		# streaming audio -> hence interruptible
		# gives direct control over played audio
		stream = sd.OutputStream(samplerate = sample_rate,
								channels = 1,
								dtype = "int16")

		try:
			with self._stream_lock:
				# thats why need to reset interrupt (else won't play anything)
				if self._interrupted.is_set():
					return

				# registering the active stream
				self._active_stream = stream

			stream.start()

			chunk_size = 2048
			for start in range(0, len(audio), chunk_size):
				# periodically checking for interruption
				if self._interrupted.is_set():
					break

				end = start + chunk_size
				stream.write(audio[start:end])

		except sd.PortAudioError:
			if not self._interrupted.is_set():
				raise

		finally:
			with self._stream_lock:
				if self._active_stream is stream:
					self._active_stream = None 

			try:
				stream.close()
			except Exception:
				pass
