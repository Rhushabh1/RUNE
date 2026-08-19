from time import perf_counter


class TurnMetrics:
	def __init__(self):
		self.turn_started = None
		self.first_token = None
		self.first_audio = None
		self.turn_finished = None


	def start(self):
		self.turn_started = perf_counter()
		self.first_token = None
		self.first_audio = None
		self.turn_finished = None


	def token_received(self):
		if self.first_token is None:
			self.first_token = perf_counter()


	def audio_started(self):
		if self.first_audio is None:
			self.first_audio = perf_counter()


	def finish(self):
		self.turn_finished = perf_counter()


	def report(self):
		if self.turn_started is None:
			return 

		def elapsed(timestamp):
			if timestamp is None:
				return None

			return round(timestamp - self.turn_started, 3)

		print("\n--------TURN METRICS--------")
		print(f"Time to first LLM token: {elapsed(self.first_token)}")
		print(f"Time to first audible response: {elapsed(self.first_audio)}")
		print(f"Total response time: {elapsed(self.turn_finished)}")
		print("----------------------------")