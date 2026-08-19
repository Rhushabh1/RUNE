import queue
import time
from collections import deque

import numpy as np 
import sounddevice as sd 
import webrtcvad

from app.transcription import Transcriber
from app.terminal_display import print_user_text


SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30
FRAME_SAMPLES = 480
FRAME_BYTES = FRAME_SAMPLES * 2

END_SILENCE_FRAMES = 50
PRE_ROLL_FRAMES = 10
MAX_UTTERANCE_SECONDS = 20

START_TIMEOUT_SECONDS = 10
PARTIAL_INTERVAL_SECONDS = 1.2


class LiveListener:
	def __init__(self):
		self.vad = webrtcvad.Vad(2)
		self.transcriber = Transcriber()


	def _to_float_audio(self, frames):
		raw_audio = b"".join(frames)
		return np.frombuffer(raw_audio,
							dtype = np.int16
							).astype(np.float32) / 32768.0


	def listen_for_utterance(self, on_speech_start = None):
		audio_queue = queue.Queue()

		def callback(in_data, frames, time_info, status):
			if status:
				pass
			audio_queue.put(bytes(in_data))

		pre_roll = deque(maxlen = PRE_ROLL_FRAMES)

		utterance_frames = []

		speech_started = False
		silence_frames = 0
		speech_streak = 0
		interruption_triggered = False

		start_time = time.monotonic()
		speech_start_time = None
		last_partial_time = start_time

		last_partial_text = ""
		# print("\nListening...")

		with sd.RawInputStream(samplerate = SAMPLE_RATE,
								blocksize = FRAME_SAMPLES,
								channels = 1,
								dtype = "int16",
								callback = callback):
			while True:
				now = time.monotonic()

				if not speech_started:
					if now - start_time > START_TIMEOUT_SECONDS:
						return None

				if speech_started:
					if (now - speech_start_time > MAX_UTTERANCE_SECONDS):
						break

				try:
					frame = audio_queue.get(timeout = 0.1)

				except queue.Empty:
					continue

				if len(frame) != FRAME_BYTES:
					continue

				is_speech = self.vad.is_speech(frame, SAMPLE_RATE)

				if not speech_started:
					if is_speech:
						speech_started = True
						speech_streak = 1
						speech_start_time = time.monotonic()

						utterance_frames.extend(pre_roll)
						utterance_frames.append(frame)

						# print("\nYou: ", end = "", flush = True)

						# if on_speech_start:
						# 	on_speech_start()

					else:
						pre_roll.append(frame)

					continue

				utterance_frames.append(frame)

				if is_speech:
					silence_frames = 0
					speech_streak += 1
				else:
					silence_frames += 1
					speech_streak = 0

				# trigger interruption only after 10 consecutive speech frames
				if (on_speech_start and not interruption_triggered and speech_streak >= 10):
					interruption_triggered = True
					on_speech_start()

				# periodically transcribe accumulated audio
				now = time.monotonic()

				if (now - last_partial_time >= PARTIAL_INTERVAL_SECONDS):
					audio = self._to_float_audio(utterance_frames)

					partial_text = self.transcriber.transcribe(audio, partial = True)

					if (partial_text and partial_text != last_partial_text):
						# print("\rYou: " + partial_text + "\033[K", end = "", flush = True)
						# print_user_text(partial_text)

						last_partial_text = partial_text

					last_partial_time = now

				if silence_frames >= END_SILENCE_FRAMES:
						break

		# final transcription after the user finishes speaking
		audio = self._to_float_audio(utterance_frames)

		final_text = self.transcriber.transcribe(audio, partial = False)

		if not final_text:
			return None

		# print("\rYou: " + final_text + "\033[K", flush = True)
		print_user_text(final_text)

		return final_text