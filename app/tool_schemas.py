# tool descriptions and calling protocol for transformer
# tells LLM what capabilities are available

TOOLS = [{
		"type": "function",
		"function": {
					"name": "get_current_time",
					"description": "Get the actual current local time and today's date. Use this whenever the user asks for the current time or date and time.",
					"parameters": {
									"type": "object",
									"properties": {},
									"required": [],
									"additionalProperties": False
									}
					}
		},
		{
		"type": "function",
		"function": {
					"name": "get_current_date",
					"description": "Get today's actual local date. Use this whenever the user asks what today's date is.",
					"parameters": {
									"type": "object",
									"properties": {},
									"required": [],
									"additionalProperties": False
									}
					}
		},
		{
		"type": "function",
		"function": {
					"name": "search_knowledge",
					"description": "Search the user's local knowledge base for information. Use this when the user asks to search, find, or retrieve information from their knowledge base.",
					"parameters": {
									"type": "object",
									"properties": {
													"query": {
															"type": "string",
															"description": "the keyword or phrase to search for"
															}
													},
									"required": ["query"],
									"additionalProperties": False
									}
					}
		}]