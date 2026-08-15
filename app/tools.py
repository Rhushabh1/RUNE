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
	if not query.strip():
		return {
				"results": []
				}

	if not KNOWLEDGE_FILE.exists():
		return {
				"error": "knowledge file not found"
				}

	content = KNOWLEDGE_FILE.read_text(encoding = "utf-8")
	matching_lines = [line.strip() for line in content.splitlines() if query.lower() in line.lower()]

	return {
			"query": query,
			"results": matching_lines[:10]
			}


# main tool registry for LLM
TOOL_REGISTRY = {
	"get_current_time": get_current_time,
	"get_current_date": get_current_date,
	"search_knowledge": search_knowledge
}