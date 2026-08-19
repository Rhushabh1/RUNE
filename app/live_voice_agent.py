import asyncio
import sys

from app.agent import stream_ask_agent
from app.tts import SpeechEngine
from app.text_chunker import TextChunker 
from app.live_listener import LiveListener
from app.terminal_display import print_agent_text
from app.conversation import (ConvState, ConversationController)
from app.latency import TurnMetrics
from app.config import (LLM_TIMEOUT_SECONDS, 
						TTS_SEGMENT_TIMEOUT_SECONDS,
						MAX_EMPTY_TURNS,
						MAX_AUDIO_QUEUE_SIZE)


SESSION_ID = "local_voice_session"


class VoiceAgentRuntime:
	def __init__(self):
		self.speaker = SpeechEngine()
		self.listener = LiveListener()

		self.controller = ConversationController()
		self.metrics = TurnMetrics()

		self.empty_turns = 0

		self.response_task = None
		self.listener_task = None


	# CONSUMER
	async def playback_worker(self, queue):
		while True:
			# reads chunks from queue -> synthesizes speech -> plays it
			text = await queue.get()
			try:
				# sneaky way to send termination signal
				if text is None:
					return 

				if self.controller.state == ConvState.THINKING:
					self.controller.transition(ConvState.SPEAKING)

				self.metrics.audio_started()

				# print(f"\n[TTS] Speaking: {text}")

				# piper synthesis and audio playback are blocking in nature
				# hence kept them off the event loop
				await asyncio.wait_for(asyncio.to_thread(self.speaker.speak, text),
										timeout = TTS_SEGMENT_TIMEOUT_SECONDS)

			finally:
				queue.task_done()


	async def generation_worker(self, message, queue):
		# to avoid excessive TTS calls & processing overhead, awkward pauses, unnatural speech
		chunker = TextChunker(max_chars = 100)
		response_text = ""

		print("\nRUNE: ", end = "", flush = True)

		async with asyncio.timeout(LLM_TIMEOUT_SECONDS):
			# yields generated token as it gets available
			async for token in stream_ask_agent(message, session_id = SESSION_ID):
				# sys.stdout.write(token)
				# sys.stdout.flush()

				self.metrics.token_received()

				response_text += token
				print_agent_text(token)

				# if a chunk gets complete, add it to the async queue
				completed_chunks = chunker.feed(token)
				for chunk in completed_chunks:
					# backpressure -> suspends until space is available
					await queue.put(chunk)

		print()

		# send any remaining text to TTS
		for chunk in chunker.flush():
			await queue.put(chunk)

		await queue.put(None)


	async def generate_and_speak(self, message):
		self.metrics.start()
		self.speaker.reset_interrupt()

		# queue -> decouples text generation from audio generation and playback
		# backpressure with maxsize -> producer waits until the queue is processed
		# allows for LLM and speech to overlap
		queue = asyncio.Queue(maxsize = MAX_AUDIO_QUEUE_SIZE)

		producer = asyncio.create_task(self.generation_worker(message, queue))
		# retrieving from queue involves waiting/blocking, so suspend this task asynchronously
		consumer = asyncio.create_task(self.playback_worker(queue))

		try:
			await asyncio.gather(producer, consumer)

		except BaseException:
			# stopping active playback before cancelling tasks
			self.speaker.interrupt()

			producer.cancel()
			consumer.cancel()

			await asyncio.gather(producer, consumer, return_exceptions = True)
			raise

		finally:
			self.metrics.finish()
			self.metrics.report()


	def on_speech_start(self):
		if self.speaker.is_playing:
			print("\n[INTERRUPTION DETECTED]", flush = True)
			self.speaker.interrupt()


	async def listen(self):
		self.controller.transition(ConvState.LISTENING)
		return await asyncio.to_thread(self.listener.listen_for_utterance, 
										self.on_speech_start)


	async def listen_during_response(self):
		return await asyncio.to_thread(self.listener.listen_for_utterance,
										self.on_speech_start)


	async def respond_to(self, message):
		self.controller.transition(ConvState.THINKING)

		# print("\nRUNE: ", end = "", flush = True)

		self.response_task = asyncio.create_task(self.generate_and_speak(message))

		self.listener_task = asyncio.create_task(self.listen_during_response())

		try:
			while True:
				done, pending = await asyncio.wait([self.response_task, self.listener_task],
													return_when = asyncio.FIRST_COMPLETED)

				# user completed a new utterance
				if self.listener_task in done:
					transcript = self.listener_task.result()

					if transcript:
						# complete user interruption has arrived
						if not self.response_task.done():
							self.controller.transition(ConvState.INTERRUPTED)

							self.speaker.interrupt()
							self.response_task.cancel()

							await asyncio.gather(self.response_task,
												return_exceptions = True)
						
						self.controller.transition(ConvState.LISTENING)

						return transcript

					# no speech detected during this listening window
					# starting another listening window
					if not self.response_task.done():
						self.listener_task = asyncio.create_task(self.listen_during_response())
						continue

				if self.response_task in done:
					await self.response_task

					if self.controller.state in {ConvState.THINKING, ConvState.SPEAKING}:
						self.controller.transition(ConvState.LISTENING)

					if self.listener_task.done():
						return self.listener_task.result()

					continue

		finally:
			if (self.listener_task and not self.listener_task.done()):
				self.listener_task.cancel()

				await asyncio.gather(self.listener_task,
									return_exceptions = True)


	# asynchronous producer-consumer design for simultaneous LLM + TTS
	# PRODUCER
	async def run(self):
		print("\033[2J\033[H", end = "", flush = True)
		print("-----------RUNE-----------")
		print("Say 'exit' or 'quit' to stop")
		print("--------------------------")
		
		try:
			# first user turn
			print("\nListening...", flush = True)
			message = await self.listen()

			# endless conversation loop
			while True:
				if not message:
					self.empty_turns += 1

					# too many empty turns (diagnostic line)
					if self.empty_turns >= MAX_EMPTY_TURNS:
						self.empty_turns = 0

					message = await self.listen()
					continue

				self.empty_turns = 0

				# exit failsafe
				if message.lower().strip() in ["exit", "exit.", "quit", "quit.", "stop assistant", "stop assistant."]:
					break

				# end = prevents newline, flush = pushes output to terminal
				# print("\nRUNE: ", end = "", flush = True)

				try:
					message = await self.respond_to(message)

				except asyncio.CancelledError:
					raise

				except Exception as e:
					self.speaker.interrupt()

					if (self.controller.state != ConvState.ERROR):
						self.controller.transition(ConvState.ERROR)

					self.controller.recover()

					message = await self.listen()

		except KeyboardInterrupt:
			print("\n[EXIT] Shutting down...")

		finally:
			self.speaker.interrupt()

			if self.response_task and not self.response_task.done():
				self.response_task.cancel()

				await asyncio.gather(self.response_task,
									return_exceptions = True)

			print("\n[EXIT] RUNE stopped")


async def main():
	runtime = VoiceAgentRuntime()
	await runtime.run()


if __name__ == "__main__":
	asyncio.run(main())