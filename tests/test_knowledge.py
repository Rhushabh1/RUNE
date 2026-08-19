from app.tools import search_knowledge, KNOWLEDGE_FILE

print("expected file: ", KNOWLEDGE_FILE)
print("file exists: ", KNOWLEDGE_FILE.exists())

result = search_knowledge("Google")

print("\nSearch result:")
print(result)