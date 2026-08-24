from pathlib import Path 

from app.memory_store import memory_store
from app.rag import rag


def rebuild():
	print("Rebuilding RAG index...")

	# remove stale entries before rebuilding source types
	rag.clear_source_type("memory")
	rag.clear_source_type("knowledge")

	# read every memory directly, without search limit
	with memory_store.connect() as conn:
		memories = conn.execute("""
							SELECT id, category, content
							FROM memory
							ORDER BY id
							""").fetchall()

	# # index all saved memories
	# memories = memory_store.search(limit = 50)

	for memory in memories:
		rag.index_text(source_type = "memory",
						source_id = str(memory["id"]),
						title = memory["category"],
						text = memory["content"],
						metadata = {
									"memory_id": memory["id"],
									"category": memory["category"]
									},
						chunk_size = 500,
						overlap = 60)

	print(f"Indexed {len(memories)} memories")

	# index the project knowledge file, if it exists
	knowledge_path = Path(__file__).resolve().parent.parent / "knowledge" / "notes.md"

	if knowledge_path.exists():
		text = knowledge_path.read_text(encoding = "utf-8")

		count = rag.index_text(source_type = "knowledge",
								source_id = "notes.md",
								title = "Project knowledge notes",
								text = text,
								metadata = {
											"filename": "notes.md"
											},
								chunk_size = 700,
								overlap = 120)

		print(f"Indexed {count} knowledge chunks")

	print("RAG index rebuild complete")


if __name__ == "__main__":
	rebuild()