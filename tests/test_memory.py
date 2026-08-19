from app.memory_store import MemoryStore 


def main():
	store = MemoryStore()

	# saving a test memory first
	memory_id = store.save(category = "test",
							content = "this is a test memory")
	print("Saved memory: ", memory_id)

	# search
	results = store.search("this")
	print("\nSearch results: ")
	for item in results:
		print(item)

	assert len(results) > 0

	# delete
	deleted = store.delete(memory_id)
	assert deleted

	# verify deletion
	results = store.search("this")
	assert all(item["id"] != memory_id for item in results)

	# clear all
	cleared = store.clear_all()
	print("\nDeleted memories: ", cleared)

	# verify table is empty
	remaining = store.search()
	print("\nRemaining memories: ", remaining)
	assert remaining == []

	print("\nAll memory tests passed")


if __name__ == "__main__":
	main()