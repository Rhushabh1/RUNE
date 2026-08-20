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
		},
		{
		"type": "function",
		"function": {
					"name": "remember_fact",
					"description": "Save information about the user into persistent SQLite long-term memory. MUST be called when the user explicitly asks to remember, save, store, or retain information. Also use it to add information provided as part of an ongoing memory-saving request. Do not merely acknowledge a save request.",
					"parameters": {
									"type": "object",
									"properties": {
													"category": {
															"type": "string",
															"description": "short category such as interests, sports, achievements, preferences, personal, work, etc."
															},
													"content": {
															"type": "string",
															"description": "the complete factual information that should be stored"
															}
													},
									"required": ["category", "content"],
									"additionalProperties": False
									}
					}
		},
		{
		"type": "function",
		"function": {
					"name": "search_memories",
					"description": "Search the persistent SQLite memory database. MUST be called when the user asks what has been remembered, what information is stored, or asks to retrieve a previously saved fact. Use an empty query to retrieve the latest memories.",
					"parameters": {
									"type": "object",
									"properties": {
													"query": {
															"type": "string",
															"description": "search phrase or keywords. use an empty string to list recent memories"
															}
													},
									"required": ["query"],
									"additionalProperties": False
									}
					}
		},
		{
		"type": "function",
		"function": {
					"name": "forget_memory",
					"description": "Delete a specific saved memory when the user explicitly asks to forget it.",
					"parameters": {
									"type": "object",
									"properties": {
													"memory_id": {
															"type": "integer",
															"description": "ID of the memory to delete"
															}
													},
									"required": ["memory_id"],
									"additionalProperties": False
									}
					}
		}]