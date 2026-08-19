from datetime import datetime
from pathlib import Path 


PROJECT_ROOT = Path(__file__).resolve().parent.parent

KNOWLEDGE_FILE = PROJECT_ROOT / "knowledge" / "notes.md"


def get_current_time():
	now = datetime.now()
	return {
			"time": now.strftime("%H:%M:%S"),
			"date": now.strftime("%Y-%m-%d")
			}


def get_current_date():
	now = datetime.now()
	return {
			"date": now.strftime("%A, %d %B %Y")
			}


# searches knowledge file for "query" keyword
def search_knowledge(query):
	if not isinstance(query, str) or not query.strip():
		return {
				"query": query,
				"results": [],
				"message": "empty or invalid search query"
				}

	# what if the file doesn't exist
	if not KNOWLEDGE_FILE.is_file():
		return {
				"error": "knowledge file not found",
				"expected_path": str(KNOWLEDGE_FILE),
				"project_root": str(PROJECT_ROOT)
				}

	try:
		# simple line matching for now -> later add proper retrieval methods
		content = KNOWLEDGE_FILE.read_text(encoding = "utf-8")

		# normalize query and lines
		search_term = query.strip().casefold()

		matching_lines = [line.strip() for line in content.splitlines() if search_term in line.casefold()]

		return {
				"query": query,
				"file": str(KNOWLEDGE_FILE),
				"total_lines": len(content.splitlines()),
				"results": matching_lines[:10],
				"result_count": len(matching_lines)
				}

	except Exception as e:
		return {
				"error": f"failed to read knowledge file: {str(e)}",
				"file": str(KNOWLEDGE_FILE)
				}


# main tool registry for LLM
TOOL_REGISTRY = {
	"get_current_time": get_current_time,
	"get_current_date": get_current_date,
	"search_knowledge": search_knowledge
}