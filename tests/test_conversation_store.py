from app.conversation_store import ConversationStore


def test_conversation_store():
	store = ConversationStore()
	session_id = "test_conversation_store"

	store.delete(session_id)

	messages = [{
				"role": "user",
				"content": "my project is called taskforge"
				},
				{
				"role": "assistant",
				"content": "i will keep that in context"
				},
				{
				"role": "assistant",
				"tool_calls": [{
								"function": {
											"name": "get_current_time",
											"arguments": {}
											}
								}]
				}]

	summary = "the user is building taskforge"

	store.save(session_id, summary, messages)

	loaded_summary, loaded_messages = store.load(session_id)

	assert loaded_summary == summary
	assert loaded_messages == messages

	sessions = store.list_sessions()
	print(sessions)
	assert any(session["session_id"] == session_id for session in sessions)

	store.delete(session_id)

	loaded_summary, loaded_messages = store.load(session_id)

	assert loaded_summary == ""
	assert loaded_messages == []

	print("Conversation store tests passed")


if __name__ == "__main__":
	test_conversation_store()