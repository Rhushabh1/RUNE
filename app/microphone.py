import sounddevice as sd 
import numpy as np 


SAMPLE_RATE = 16000
CHANNELS = 1


# records audio for a fixed duration and returns the sample
def record_audio(duration = 5):
	print(f"Recording audio for {duration} seconds...")

	audio = sd.rec(int(duration * SAMPLE_RATE),
					samplerate = SAMPLE_RATE,
					channels = CHANNELS,
					dtype = "float32")

	# wait till the recording is finished
	sd.wait()
	print("Recording is complete")

	# returns numpy array
	return audio.flatten()