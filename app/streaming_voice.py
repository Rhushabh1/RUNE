import asyncio
import sys

from app.ollama_agent import stream_ask_agent
from app.tts import SpeechEngine
from app.text_chunker import TextChunker 


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

			print(f"\n[TTS] Speaking: {text}")

			# piper synthesis and audio playback are blocking in nature
			# hence kept them off the event loop
			await asyncio.to_thread(speaker.speak, text)

		finally:
			queue.task_done()


# asynchronous producer-consumer design for simultaneous LLM + TTS
# PRODUCER
async def main():
	speaker = SpeechEngine()
	# queue -> decouples text generation from audio generation and playback
	# backpressure with maxsize -> producer waits until the queue is processed
	# allows for LLM and speech to overlap
	queue = asyncio.Queue(maxsize = 3)
	# to avoid excessive TTS calls & processing overhead, awkward pauses, unnatural speech
	chunker = TextChunker(max_chars = 180)
	# retrieving from queue involves waiting/blocking, so suspend this task asynchronously
	worker = asyncio.create_task(playback_worker(queue, speaker))

	try:
		# endless conversation loop
		while True:
			message = input("\nYou: ").strip()
			# exit failsafe
			if message.lower() in ["exit", "quit", "q"]:
				break
			if not message:
				continue

			# end = prevents newline, flush = pushes output to terminal
			print("\nRUNE: ", end = "", flush = True)

			# yields generated token as it gets available
			async for token in stream_ask_agent(message, session_id = SESSION_ID):
				sys.stdout.write(token)
				sys.stdout.flush()

				# if a chunk gets complete, add it to the async queue
				completed_chunks = chunker.feed(token)
				for chunk in completed_chunks:
					# backpressure -> suspends until space is available
					await queue.put(chunk)

			# send any remaining text to TTS
			for chunk in chunker.flush():
				await queue.put(chunk)

			print("\n")

			# wait until all generated speech has played out
			# waits for queue.task_done() on each queue item
			await queue.join()

	finally:
		await queue.put(None)
		await worker 


if __name__ == "__main__":
	asyncio.run(main())