from app.memory_store import memory_store


def test_memory_retrieval():
	test_memory_ids = []

	try:
		# saving a few statements to memory store
		test_memory_ids.append(memory_store.save("project",
												"taskforge uses postgresql, redis and kafka"))
		test_memory_ids.append(memory_store.save("project",
												"tradelab uses FAISS for vector-based document retrieval"))

		# searching if it retrieves taskforge with good relevance score
		results = memory_store.search("which database does taskforge use?",
										limit = 5)

		assert results
		assert "taskforge" in results[0]["content"]
		assert results[0]["relevance_score"] > 0

		# searching if it retrieves faiss too
		results = memory_store.search("FAISS document retrieval",
										limit = 5)

		assert results
		assert "FAISS" in results[0]["content"]

		print("All memory retrieval tests passed")

	finally:
		# memory IDs cleanup
		for memory_id in test_memory_ids:
			memory_store.delete(memory_id)


if __name__ == "__main__":
	test_memory_retrieval()
