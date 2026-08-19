# because httpx supports asynchronous operations
import httpx
import json
from typing import AsyncIterator

from app.tool_schemas import TOOLS 
from app.tool_executor import execute_tool


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

Tool usage:
- You MUST call get_current_time when asked for the current time.
- You MUST call get_current_date when asked for today's date.
- You MUST call search_knowledge when asked to search or retrieve information from the knowledge base.
- Never invent current dates, times, or knowledge base search results.
- After receiving a tool result, use that result to formulate your answer.
- Do not display tool-call syntax, XML, JSON, or internal tool instructions to the user.
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
		# for rollback
		original_history_length = len(history)
		history.append({
						"role": "user",
						"content": message
						})

		try:
			# create http client to send/receive requests
			async with httpx.AsyncClient(timeout = 120.0) as client:
				# only 3 tool calls allowed for now
				for _ in range(3):

					# send http POST request
					response = await client.post(f"{OLLAMA_URL}/api/chat",
												json = {
														"model": MODEL,
														"messages": history,
														"tools": TOOLS,
														"think": False,
														"stream": False
														})

					# check if request succeeded -> return status code
					response.raise_for_status()

					# unparse json via python dictionary
					msg = response.json()["message"]

					# print("\n[OLLAMA] ", json.dumps(msg, indent=2))
					# print("\nTool calls: ", msg.get("tool_calls"))
					# print(f"\nRUNE: {answer}", flush = True)
					history.append(msg)

					tool_calls = msg.get("tool_calls", [])
					if not tool_calls:
						answer = msg.get("content", "").strip()
						return answer

					for tool_call in tool_calls:
						function_data = tool_call["function"]
						tool_name = function_data["name"]
						args = function_data.get("arguments", {})

						if isinstance(args, str):
							args = json.loads(args)

						result = execute_tool(tool_name, args)
						# print("Result: ", result)

						history.append({
										"role": "tool",
										"tool_name": tool_name,
										"content": result
										})

				raise RuntimeError("max tool execution limit exceeded")
				
			# history.append({
			# 				"role": "assistant",
			# 				"content": answer
			# 				})
			# return answer

		except Exception:
			del history[original_history_length:]
			raise


	# using streaming and thinking utility of ollama
	async def stream_respond(self, message, session_id = "default") -> AsyncIterator[str]:
		history = self.get_history(session_id)
		# for rollback
		original_history_length = len(history)
		history.append({
						"role": "user",
						"content": message
						})

		try:
			# create http client to send/receive requests
			async with httpx.AsyncClient(timeout = 120.0) as client:
				# only 3 tool calls allowed for now
				for _ in range(3):
					payload = {
								"model": MODEL,
								"messages": history,
								"tools": TOOLS,
								# thinking consumes time and increases audio delay
								"think": False,
								"stream": True
								}

					answer = []
					tool_calls = []
					# thinking_started = False
					response_started = False

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

							# collect structured tool calls
							current_tool_calls = msg.get("tool_calls", [])
							if current_tool_calls:
								tool_calls.extend(current_tool_calls)

							if chunk.get("done"):
								break

					# print()

					complete_response = "".join(answer).strip()

					if not tool_calls:
						history.append({
										"role": "assistant",
										"content": complete_response
										})
						return

					# preserve assistant's tool call message in history
					msg = {
							"role": "assistant",
							"content": complete_response,
							"tool_calls": tool_calls
							}
					history.append(msg)

					# execute the tool calls
					for tool_call in tool_calls:
						function_data = tool_call["function"]
						tool_name = function_data["name"]
						args = function_data.get("arguments", {})

						# handle args returned as json strings
						if isinstance(args, str):
							args = json.loads(args)

						result = execute_tool(tool_name, args)

						# send tool result back to ollama
						history.append({
										"role": "tool",
										"tool_name": tool_name,
										"content": result
										})

				raise RuntimeError("max tool execution limit exceeded")

		except Exception:
			del history[original_history_length:]
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