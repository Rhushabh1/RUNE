import time
import asyncio
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# decide which model to load
# temporary arrangement before replaced by Ollama
MODEL_NAME = "HuggingFaceTB/SmolLM2-360M-Instruct"
SYSTEM_PROMPT = """ 
You are RUNE, a personal AI assistant.

Instructions:
1. Answer the user's latest question directly.
2. Carefully consider the entire conversation history.
3. Remember facts explicitly provided by the user during this conversation.
4. If the user tells you their name, use that information when asked.
5. Never introduce yourself unless the user asks you to.
6. Do not repeat previous answers unless relevant.
7. If you do not know something, say so honestly.
8. Keep responses concise and natural.
"""
MAX_NEW_TOKENS = 100

print("Loading tokenizer...")
# to track model loading time
start_time = time.time()
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
# model test run
model.eval()
print(f"Model loaded in {time.time() - start_time} seconds")


# main conversational agent used by voice assistant
class Agent:
	def __init__(self):
		self.sessions = {}
		# shared lock to prevent simultaneous generation runs at a time
		self.lock = asyncio.Lock()

	# get conversation history for a session
	def get_history(self, session_id):
		if session_id not in self.sessions:
			self.sessions[session_id] = [{
										"role": "system",
										"content": SYSTEM_PROMPT
										}]
		return self.sessions[session_id]

	# run synchronous transformer inference
	def generate_response(self, history):
		# converting message into input tokens
		# explicitly request a dictionary containing pytorch tensors
		inputs = tokenizer.apply_chat_template(history,
												add_generation_prompt = True,
												tokenize = True,
												return_tensors = "pt",
												return_dict = True)
		
		with torch.inference_mode():
			# calling model to return output
			outputs = model.generate(**inputs,
									max_new_tokens = MAX_NEW_TOKENS,
									do_sample = False,
									pad_token_id = tokenizer.eos_token_id,
									# repetition check & penalty
									repetition_penalty = 1.1)

		# extract only newly generated tokens
		input_length = inputs["input_ids"].shape[-1]
		# stripping for output tokens
		generated_tokens = outputs[0][input_length:]
		
		# converting output tokens into back into text
		response = tokenizer.decode(generated_tokens,
									skip_special_tokens = True
									).strip()
		return response

	# asynchronously generate response while maintaining conversation history
	async def respond(self, message, session_id = "default"):
		# to prevent empty messages from entering history
		message = message.strip()
		if not message:
			return ""

		async with self.lock:
			history = self.get_history(session_id)
			history.append({
							"role": "user",
							"content": message
							})
			try:
				# print("\nConversation before inference")
				# for item in history:
				# 	print(f"{item["role"]}: {item["content"]}")
				response = await asyncio.to_thread(self.generate_response, 
													history)
				history.append({
								"role": "assistant",
								"content": response
								})
				return response
			except Exception:
				# rollback the failed user message
				history.pop()
				raise

	# clear conversation history for a session
	def clear_session(self, session_id = "default"):
		self.sessions.pop(session_id, None)


# shared agent instance
agent = Agent()

async def ask_agent(message, session_id = "default"):
	return await agent.respond(message, session_id)
