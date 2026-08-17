import asyncio
import sys

from app.agent import stream_ask_agent
from app.tts import SpeechEngine
from app.text_chunker import TextChunker 
from app.live_listener import LiveListener
from app.terminal_display import print_agent_text


SESSION_ID = "local_voice_session"


# CONSUMER
async def playback_worker(queue, speaker):
	while True:
		# reads chunks from queue -> synthesizes speech -> plays it
		text = await queue.get()
		try:
			# sneaky way to send termination signal
			if text is None:
				return 

			# print(f"\n[TTS] Speaking: {text}")

			# piper synthesis and audio playback are blocking in nature
			# hence kept them off the event loop
			await asyncio.to_thread(speaker.speak, text)

		finally:
			queue.task_done()


async def generation_worker(message, queue):
	# to avoid excessive TTS calls & processing overhead, awkward pauses, unnatural speech
	chunker = TextChunker(max_chars = 180)
	response_text = ""

	# yields generated token as it gets available
	async for token in stream_ask_agent(message, session_id = SESSION_ID):
		# sys.stdout.write(token)
		# sys.stdout.flush()

		response_text += token
		print_agent_text(response_text)

		# if a chunk gets complete, add it to the async queue
		completed_chunks = chunker.feed(token)
		for chunk in completed_chunks:
			# backpressure -> suspends until space is available
			await queue.put(chunk)

	# send any remaining text to TTS
	for chunk in chunker.flush():
		await queue.put(chunk)

	await queue.put(None)


async def run_response(message, speaker):
	speaker.reset_interrupt()

	# queue -> decouples text generation from audio generation and playback
	# backpressure with maxsize -> producer waits until the queue is processed
	# allows for LLM and speech to overlap
	queue = asyncio.Queue(maxsize = 3)

	producer = asyncio.create_task(generation_worker(message, queue))
	# retrieving from queue involves waiting/blocking, so suspend this task asynchronously
	consumer = asyncio.create_task(playback_worker(queue, speaker))

	try:
		await asyncio.gather(producer, consumer)

	except BaseException:
		# stopping active playback before cancelling tasks
		speaker.interrupt()

		producer.cancel()
		consumer.cancel()

		await asyncio.gather(producer, consumer, return_exceptions = True)
		raise


async def listen_while_responding(listener, speaker, response_task):
	def on_speech_start():
		if speaker.is_playing:
			print("\033[8;1H\033[2K[INTERRUPTION DETECTED]", flush = True)
			speaker.interrupt()

	listener_task = asyncio.create_task(asyncio.to_thread(listener.listen_for_utterance,
														on_speech_start))

	try:
		while True:
			done, pending = await asyncio.wait([response_task, listener_task],
												return_when = asyncio.FIRST_COMPLETED)

			if listener_task in done:
				transcript = listener_task.result()

				if transcript:
					# complete user interruption has arrived
					speaker.interrupt()

					if not response_task.done():
						response_task.cancel()

					await asyncio.gather(response_task,
										return_exceptions = True)
					return transcript

				# no speech detected during this listening window
				# starting another listening window
				if not response_task.done():
					listener_task = asyncio.create_task(asyncio.to_thread(listener.listen_for_utterance,
																		on_speech_start))
					continue

			if response_task in done:
				await response_task

				# response is finished and wait for next user turn
				transcript = await listener_task
				return transcript
	finally:
		if not listener_task.done():
			listener_task.cancel()

			await asyncio.gather(listener_task,
								return_exceptions = True)


# asynchronous producer-consumer design for simultaneous LLM + TTS
# PRODUCER
async def main():
	speaker = SpeechEngine()
	listener = LiveListener()

	print("\033[2J\033[H", end = "", flush = True)
	print("-----------RUNE-----------")
	print("Say 'exit' or 'quit' to stop")
	print("--------------------------")
	
	try:
		# first user turn
		print("\nListening...", flush = True)
		message = await asyncio.to_thread(listener.listen_for_utterance)

		# endless conversation loop
		while True:
			if not message:
				message = await asyncio.to_thread(listener.listen_for_utterance)
				continue

			# exit failsafe
			if message.lower().strip() in ["exit", "exit.", "quit", "quit.", "stop assistant", "stop assistant."]:
				break

			# end = prevents newline, flush = pushes output to terminal
			# print("\nRUNE: ", end = "", flush = True)

			response_task = asyncio.create_task(run_response(message, speaker))

			# listen concurrently with LLM + playback
			message = await listen_while_responding(listener, speaker, response_task)

			# print("\n")

	except KeyboardInterrupt:
		print("\n[EXIT] Shutting down...")

	finally:
		speaker.interrupt()


if __name__ == "__main__":
	asyncio.run(main())