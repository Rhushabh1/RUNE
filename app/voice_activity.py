import time
from collections import deque
import numpy as np 
import sounddevice as sd 
# it supports only in multiples of 8000 (not 22050)
import webrtcvad


# VAD configurations
# audio sampling frequency (in hertz = samples per second)
SAMPLE_RATE = 16000
# audio chunk size
FRAME_DURATION_MS = 30
FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
# int16 = 2 bytes
FRAME_BYTES = FRAME_SAMPLES * 2
# speech detection sensitivity
VAD_MODE = 2
# preserve the beginning of speech
PRE_ROLL_MS = 300
# determine when a turn ends
END_SILENCE_MS = 1500
# prevent indefinite recording
MAX_UTTERANCE_SECONDS = 20
# avoid waiting indefinitely
START_TIMEOUT_SECONDS = 10



# records one utterance using VAD and returns float32 audio samples
def record_utterance():
	vad = webrtcvad.Vad(VAD_MODE)

	# calculate exact frames to look out for
	pre_roll_frames = PRE_ROLL_MS // FRAME_DURATION_MS
	silence_frames_required = END_SILENCE_MS // FRAME_DURATION_MS
	max_frames = int(MAX_UTTERANCE_SECONDS * 1000 / FRAME_DURATION_MS)

	# deque to store the preserved frames
	pre_roll = deque(maxlen = pre_roll_frames)
	recorded_frames = []

	speech_started = False
	silence_frames = 0

	print("\nListening...")

	start_time = time.monotonic()

	with sd.RawInputStream(samplerate = SAMPLE_RATE,
							blocksize = FRAME_SAMPLES,
							channels = 1,
							dtype = "int16"
							) as stream:
		while True:
			frame, overflowed = stream.read(FRAME_SAMPLES)
			if overflowed:
				print("Warning: microphone input overflowed")
				
			frame = bytes(frame)
			if len(frame) != FRAME_BYTES:
				continue

			is_speech = vad.is_speech(frame, SAMPLE_RATE)


			if not speech_started:
				# append to pre_roll for speech/non-speech preservation
				pre_roll.append(frame)

				if is_speech:
					speech_started = True
					print("Speech detected")
					recorded_frames.extend(pre_roll)
				# speech undetected for too long
				elif (time.monotonic() - start_time > START_TIMEOUT_SECONDS):
					print("No speech detected")
					# return empty audio frames array
					return np.array([], dtype = np.float32)

			else:
				# directly append as recorded frame
				recorded_frames.append(frame)

				if is_speech:
					silence_frames = 0
				else:
					silence_frames += 1

				# silent for too long
				if silence_frames >= silence_frames_required:
					print("End of speech detected")
					break
				# recording for too long
				if len(recorded_frames) >= max_frames:
					print("Max utterance duration reached")
					break

	audio_bytes = b"".join(recorded_frames)
	audio = np.frombuffer(audio_bytes,
						dtype = np.int16
						).astype(np.float32)

	audio /=32768.0

	return audio
