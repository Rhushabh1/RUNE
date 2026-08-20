from datetime import datetime
from pathlib import Path 

from app.memory_store import memory_store


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


# to save memory to the sqlite3 DB
def remember_fact(category, content):
	print("[MEMORY] DB:", memory_store.db_path)
	# fetch memory ID for the memory, as proof of save
	memory_id = memory_store.save(category = category,
									content = content)

	print("[MEMORY] SAVED:", memory_id)
	return {
			"success": True,
			"memory_id": memory_id,
			"message": "Memory saved"
			}


# to search for specific query in memories DB
def search_memories(query = None):
	print("[MEMORY] SEARCH QUERY:", query)
	print("[MEMORY] DB:", memory_store.db_path)
	results = memory_store.search(query = query,
									limit = 10)
	
	print("[MEMORY] RESULTS:", results)
	return {
			"success": True,
			"memories": results
			}


# to delete specific memory from the memory DB
def forget_memory(memory_id):
	deleted = memory_store.delete(memory_id = memory_id)
	return {
			"success": deleted,
			"message": "Memory deleted" if deleted else "Memory not found"
			}


# main tool registry for LLM
TOOL_REGISTRY = {
	"get_current_time": get_current_time,
	"get_current_date": get_current_date,
	"search_knowledge": search_knowledge,
	"remember_fact": remember_fact,
	"search_memories": search_memories,
	"forget_memory": forget_memory
}