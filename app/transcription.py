from faster_whisper import WhisperModel


# local STT using whisper flow model
class Transcriber:
	def __init__(self, model_type = "base"):
		print("[ASR] Loading Whisper model...")
		self.model = WhisperModel(model_type,
									device = "cpu",
									compute_type = "int8")
		print("[ASR] Whisper ready")


	# converts recorded audio into text at once (no streamed input)
	def transcribe(self, audio, partial = False):
		segments, info = self.model.transcribe(audio,
												language = "en",
												# partial is faster -> intended for live display
												beam_size = 1 if partial else 5,
												vad_filter = not partial)

		text = " ".join(segment.text.strip() for segment in segments)

		return text.strip()

