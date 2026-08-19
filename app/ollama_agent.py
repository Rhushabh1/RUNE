# because httpx supports asynchronous operations
import httpx
import json


# ollama configurations
# ollama's default server port
OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen3:0.6b"


# simple crude ollama agent llm responses
async def ask_agent(message):
	payload = {
				"model": MODEL,
				"messages": [{
							"role": "system",
							"content": "You are RUNE - personal AI voice assistant. Keep your answers clear and concise."
							},
							{
							"role": "user",
							"content": message
							}],
				# want complete answers (no intermediate tokens)
				"stream": False
				}

	# create http client to send/receive requests
	async with httpx.AsyncClient(timeout = 120.0) as client:
		# send http POST request
		response = await client.post(f"{OLLAMA_URL}/api/chat",
									json = payload)

		# check if request succeeded -> return status code
		response.raise_for_status()

		# unparse json via python dictionary
		answer = response.json()["message"]["content"].strip()
		print(f"\nRUNE: {answer}", flush = True)
		
		return answer


# using streaming and thinking utility of ollama
async def stream_ask_agent(message):
	payload = {
				"model": MODEL,
				"messages": [{
							"role": "system",
							"content": "You are RUNE - personal AI voice assistant. Keep your answers clear and concise."
							},
							{
							"role": "user",
							"content": message
							}],
				# thinking consumes time and increases audio delay
				"think": False,
				"stream": True
				}

	answer = []
	thinking_started = False
	response_started = False

	# create http client to send/receive requests
	async with httpx.AsyncClient(timeout = 120.0) as client:
		# open http POST request stream
		async with client.stream("POST",
								f"{OLLAMA_URL}/api/chat",
								json = payload
								) as response:
			response.raise_for_status()

			async for line in response.aiter_lines():
				if not line:
					continue

				# decoding json into python dict
				chunk = json.loads(line)
				msg = chunk.get("message", {})

				thinking = msg.get("thinking", "")
				content = msg.get("content", "")

				# displaying thinking separately from final response
				if thinking:
					if not thinking_started:
						print("\n[THINKING]")
						thinking_started = True

					print(thinking, end = "", flush = True)

				# displaying final response
				if content:
					if not response_started:
						print("\nRUNE: ", end = "", flush = True)
						response_started = True
						
					print(content, end = "", flush = True)
					answer.append(content)

				if chunk.get("done"):
					break

		print()

		return "".join(answer).strip()


