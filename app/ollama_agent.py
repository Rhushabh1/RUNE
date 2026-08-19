# because httpx supports asynchronous operations
import httpx
import json
from typing import AsyncIterator


# ollama configurations
# ollama's default server port
OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen3:0.6b"
SYSTEM_PROMPT = """ 
You are RUNE, a personal AI voice assistant of the user.

Instructions:
- Answer the user's latest question directly.
- Carefully consider the entire conversation history.
- Remember facts explicitly provided by the user during this conversation.
- Do not repeat previous answers unless relevant.
- If you do not know something, say so honestly.
- Keep responses concise and conversational.
"""


# turning it into a class for modularity & abstraction
class OllamaAgent:
	def __init__(self):
		# each sessioin should have independent history
		self.sessions = {}


	def get_history(self, session_id):
		if session_id not in self.sessions:
			# setting up the first system prompt in history
			self.sessions[session_id] = [{
										"role": "system",
										"content": SYSTEM_PROMPT
										}]
		return self.sessions[session_id]


	async def respond(self, message, session_id = "default"):
		history = self.get_history(session_id)
		history.append({
						"role": "user",
						"content": message
						})

		try:
			# create http client to send/receive requests
			async with httpx.AsyncClient(timeout = 120.0) as client:
				# send http POST request
				response = await client.post(f"{OLLAMA_URL}/api/chat",
											json = {
													"model": MODEL,
													"messages": history,
													"think": False,
													"stream": False
													})

				# check if request succeeded -> return status code
				response.raise_for_status()

				# unparse json via python dictionary
				answer = response.json()["message"]["content"].strip()
				# print(f"\nRUNE: {answer}", flush = True)
				
			history.append({
							"role": "assistant",
							"content": answer
							})
			return answer

		except Exception:
			history.pop()
			raise


	# using streaming and thinking utility of ollama
	async def stream_respond(self, message, session_id = "default") -> AsyncIterator[str]:
		history = self.get_history(session_id)
		history.append({
						"role": "user",
						"content": message
						})

		try:
			payload = {
						"model": MODEL,
						"messages": history,
						# thinking consumes time and increases audio delay
						"think": False,
						"stream": True
						}

			answer = []
			# thinking_started = False
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

						# thinking = msg.get("thinking", "")
						content = msg.get("content", "")

						# # displaying thinking separately from final response
						# if thinking:
						# 	if not thinking_started:
						# 		print("\n[THINKING]")
						# 		thinking_started = True

						# 	print(thinking, end = "", flush = True)

						# displaying final response
						if content:
							if not response_started:
								# print("\nRUNE: ", end = "", flush = True)
								response_started = True
								
							# print(content, end = "", flush = True)
							answer.append(content)
							yield content

						if chunk.get("done"):
							break

				# print()

				complete_response = "".join(answer).strip()
				history.append({
								"role": "assistant",
								"content": complete_response
								})

		except Exception:
			history.pop()
			raise


	def clear_session(self, session_id):
		self.sessions.pop(session_id, None)


# shared instance across application
agent = OllamaAgent()


async def ask_agent(message, session_id = "default"):
	return await agent.respond(message, session_id)


# streams one token chunk at a time
async def stream_ask_agent(message, session_id = "default"):
	async for chunk in agent.stream_respond(message, session_id):
		yield chunk