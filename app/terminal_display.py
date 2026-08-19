def print_user_text(text):
	# move to user transcription line (row 1)
	# print(f"\033[5;1H\033[2KYou: {text}", end = "", flush = True)
	print(f"\nYou: {text}", flush = True)


def print_agent_text(text):
	# move to agent's response line (row 2)
	# print(f"\033[7;1H\033[2KRUNE: {text}", end = "", flush = True)
	print(text, end = "", flush = True)