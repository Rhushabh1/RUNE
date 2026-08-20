from app.memory_store import memory_store


def main():
	while True:
		print("\n------MEMORY MANAGER------")
		print("1. View memories")
		print("2. Search memories")
		print("3. Delete memory")
		print("4. Clear all memories")
		print("5. Exit")
		print("--------------------------")

		choice = input("\nSelect: ").strip()

		if choice == "1":
			# lookup all memories at once
			results = memory_store.search(limit = 10)
			
			for item in results:
				print(f"\nID: {item["id"]}")
				print(f"Category: {item["category"]}")
				print(f"Content: {item["content"]}")

		elif choice == "2":
			query = input("Search: ")

			# to search memories for query phrase
			results = memory_store.search(query)
			
			for item in results:
				print(item)

		elif choice == "3":
			memory_id = int(input("Memory ID: "))
			
			# delete this specific memory ID
			if memory_store.delete(memory_id):
				print("Deleted")
			
			else:
				print("Memory not found")

		elif choice == "4":
			confirmation = input("Type DELETE ALL to confirm: ")

			# best way to get confirmation
			if confirmation == "DELETE ALL":
				memory_store.clear_all()
				print("All memories cleared")

		elif choice == "5":
			# exit the endless conversation loop
			break



if __name__ == "__main__":
	main()