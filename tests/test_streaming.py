import asyncio
import sys
import time

from app.ollama_agent import stream_ask_agent


async def main():
	session_id = "streaming_test"

	# endless conversation loop
	while True:
		message = input("\nYou: ").strip()
		if not message:
			continue
		# exit failsafe
		if message.lower() in ["exit", "quit"]:
			break

		print("\nRUNE: ", end = "", flush = True)

		# capturing start & end times for metrics
		start_time = time.perf_counter()
		first_token_time = None

		# loading token chunk one by one
		async for chunk in stream_ask_agent(message, session_id = session_id):
			if first_token_time is None:
				first_token_time = time.perf_counter()

			# write first chunk to the output screen
			sys.stdout.write(chunk)
			sys.stdout.flush()

		end_time = time.perf_counter()

		print("\n")

		# printing time metrics
		if first_token_time is not None:
			print(f"Time to first output: {round(first_token_time - start_time, 3)} seconds")
		print(f"Total generation time: {round(end_time - start_time, 3)} seconds")


if __name__ == "__main__":
	asyncio.run(main())