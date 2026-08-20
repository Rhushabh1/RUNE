import json
import sqlite3
from datetime import datetime
from pathlib import Path 
from contextlib import contextmanager


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "voice_agent.db"

SQLITE_TIMEOUT_SECONDS = 10


# to create DB table to store conversation history/summaries
class ConversationStore:
	def __init__(self, db_path = DB_PATH):
		self.db_path = Path(db_path).resolve()
		self.db_path.parent.mkdir(parents = True, exist_ok = True)
		
		self.initialize()


	# a common connection for all functions/db operations
	@contextmanager
	def connect(self):
		conn = sqlite3.connect(self.db_path,
								timeout = SQLITE_TIMEOUT_SECONDS)

		# to enable foreign key enforcement and ensure cascading works
		conn.execute("PRAGMA foreign_keys = ON")
		conn.row_factory = sqlite3.Row 
		
		try:
			yield conn 
			conn.commit()

		except Exception:
			conn.rollback()
			raise

		finally:
			conn.close()


	# sets the DB tables for conversation history
	def initialize(self):
		with self.connect() as conn:
			# to store summary
			conn.execute(f"""
						CREATE TABLE IF NOT EXISTS conversations (
							session_id TEXT PRIMARY KEY,
							summary TEXT NOT NULL DEFAULT '',
							updated_at TEXT NOT NULL
						)
						""")

			# to store chat history
			conn.execute(f"""
						CREATE TABLE IF NOT EXISTS conversation_messages (
							id INTEGER PRIMARY KEY AUTOINCREMENT,
							session_id TEXT NOT NULL,
							sequence INTEGER NOT NULL,
							payload TEXT NOT NULL,
							FOREIGN KEY(session_id)
								REFERENCES conversations(session_id)
								ON DELETE CASCADE,
							UNIQUE(session_id, sequence)
						)
						""")

			# for recent session ID and sequence
			conn.execute("""
						CREATE INDEX IF NOT EXISTS idx_conversation_messages
						ON conversation_messages(session_id, sequence)
						""")


	# loading conversation summary and chat history for a specific session_id
	def load(self, session_id):
		with self.connect() as conn:
			# extract summary
			conversation = conn.execute("""
										SELECT summary 
										FROM conversations 
										WHERE session_id = ?
										""",
										(session_id,)
										).fetchone()

			if conversation is None:
				return "", []

			# pulling chat history
			rows = conn.execute("""
								SELECT payload
								FROM conversation_messages
								WHERE session_id = ?
								ORDER BY sequence
								""",
								(session_id,)
								).fetchall()

		messages = [json.loads(row["payload"]) for row in rows]

		return conversation["summary"], messages


	# saving summary and chat history for a specific session_id
	def save(self, session_id, summary, messages):
		now = datetime.now().isoformat()

		with self.connect() as conn:
			# save summary
			conn.execute("""
						INSERT INTO conversations (session_id, summary, updated_at)
						VALUES (?, ?, ?)
						ON CONFLICT(session_id) DO UPDATE SET
							summary = excluded.summary,
							updated_at = excluded.updated_at
						""",
						(session_id, summary, now))

			# delete old chat history for overwriting it
			conn.execute("""
						DELETE FROM conversation_messages
						WHERE session_id = ?
						""",
						(session_id,))

			# save chat history
			conn.executemany("""
							INSERT INTO conversation_messages (session_id, sequence, payload)
							VALUES (?, ?, ?)
							""",
							[(session_id, index, json.dumps(message)) for index, message in enumerate(messages)])


	# completely deleting the session_id from DB
	def delete(self, session_id):
		with self.connect() as conn:
			# the delete cascade should take care of the rest deletions
			conn.execute("""
						DELETE FROM conversations
						WHERE session_id = ?
						""",
						(session_id,))


	# returns a list of all sessions with their last updated time
	def list_sessions(self):
		with self.connect() as conn:
			rows = conn.execute("""
								SELECT session_id, updated_at
								FROM conversations
								ORDER BY updated_at DESC
								"""
								).fetchall()

			return [dict(row) for row in rows]


conversation_store = ConversationStore()
