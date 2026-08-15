import json

from app.tools import TOOL_REGISTRY


# controls what agent is allowed to execute
# executes tool matching in the tool_registry
def execute_tool(name, arguments):
	if name not in TOOL_REGISTRY:
		return json.dumps({
							"error": "Tool not found"
						})

	if not isinstance(arguments, dict):
		return json.dumps({
							"error": "Invalid tool arguments"
						})

	try:
		function = TOOL_REGISTRY[name]

		# tool with arguments
		if name == "search_knowledge":
			query = arguments.get("query")
			if not isinstance(query, str):
				raise ValueError("query must be a string")
			result = function(query = query)

		# tool with no arguments
		else:
			if arguments:
				raise ValueError("This tool accepts no arguments")
			result = function()

		return json.dumps(result)

	except Exception as e:
		return json.dumps({
							"error": str(e)
						})