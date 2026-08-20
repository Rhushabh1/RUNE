import json

from app.tools import TOOL_REGISTRY


# makes verifying arguments easy
TOOL_ARGUMENTS = {
				"get_current_time": set(),
				"get_current_date": set(),
				"search_knowledge": {"query"},
				"remember_fact": {"category", "content"},
				"search_memories": {"query"},
				"forget_memory": {"memory_id"}
				}


# controls what agent is allowed to execute
# executes tool matching in the tool_registry
def execute_tool(name, arguments):
	# validating tool existence
	if name not in TOOL_REGISTRY:
		return json.dumps({
							"success": False,
							"error": f"Unknown tool: {name}"
						})

	# validating arguments
	if not isinstance(arguments, dict):
		return json.dumps({
							"success": False,
							"error": "Invalid tool arguments. Tool arguments must be an object."
						})

	allowed = TOOL_ARGUMENTS[name]

	# reject unexpected arguments
	unexpected = set(arguments) - allowed
	if unexpected:
		return json.dumps({
							"success": False,
							"error": f"Unexpected arguments: {unexpected}"
							})

	missing = TOOL_ARGUMENTS.get(name, set()) - set(arguments)
	if missing:
		return json.dumps({
							"success": False,
							"error": f"Missing arguments: {missing}"
							})

	try:
		# finally execute the tool call function
		result = TOOL_REGISTRY[name](**arguments)

		return json.dumps({
							"success": True,
							"result": result
							}, ensure_ascii = False)
	
	except Exception as e:
		return json.dumps({
							"success": False,
							"error": str(e)
							}, ensure_ascii = False)