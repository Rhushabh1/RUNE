from faster_whisper import WhisperModel


# local STT using whisper flow model
class SpeechInput:
	def __init__(self):
		print("Loading Whisper model...")
		self.model = WhisperModel("base",
									device = "cpu",
									compute_type = "int8")

	# converts recorded audio into text at once (no streamed input)
	def transcribe(self, audio):
		segments, info = self.model.transcribe(audio,
												language = "en",
												vad_filter = True)

		text = " ".join(segment.text.strip() for segment in segments)

		return text.strip()

