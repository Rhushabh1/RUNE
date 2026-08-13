import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# decide which model to load
# temporary arrangement before replaced by Ollama
MODEL_NAME = "HuggingFaceTB/SmolLM2-360M-Instruct"
print("Loading tokenizer...")
# to track model loading time
start_time = time.time()
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
# model test run
model.eval()
print(f"Model loaded in {time.time() - start_time} seconds")
print("Device : CPU (no CUDA available)")



# for temporary conversation history & persistence (only for current runtime session)
conversation_history = [{
						"role": "system",
						"content": "You are RUNE - a personal AI assistant. Answer clearly and concisely."
						}]

# main function which calls LLM for response
def ask_llm(question):
	global conversation_history

	# add only the latest user message
	conversation_history.append({
								"role": "user",
								"content": question
								})

	# converting message into input tokens
	# explicitly request a dictionary containing pytorch tensors
	inputs = tokenizer.apply_chat_template(conversation_history,
											add_generation_prompt = True,
											tokenize = True,
											return_tensors = "pt",
											return_dict = True)
	with torch.inference_mode():
		# calling model to return output
		outputs = model.generate(**inputs,
								max_new_tokens = 100,
								do_sample = False,
								pad_token_id = tokenizer.eos_token_id)

	# extract only newly generated tokens
	input_length = inputs["input_ids"].shape[-1]
	# stripping for output tokens
	generated_tokens = outputs[0][input_length:]
	
	# converting output tokens into back into text
	response = tokenizer.decode(generated_tokens,
								skip_special_tokens = True
								).strip()
	# save llm's response to history
	conversation_history.append({
								"role": "assistant",
								"content": response
								})
	return response


if __name__ == "__main__":
	print("\nRUNE LLM at your service!")

	# endless conversation loop with RUNE
	while True:
		question = input("\nYou: ")
		# exit failsafe
		if question.lower() in ["exit", "quit"]:
			break
		response = ask_llm(question)
		print(f"\nRUNE: {response}")