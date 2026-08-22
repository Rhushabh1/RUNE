import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path 
from datetime import datetime


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "voice_agent.db"

# DB constants
SCHEMA_VERSION = 1

MAX_CATEGORY_LENGTH = 50
MAX_CONTENT_LENGTH = 2000
DEFAULT_SEARCH_LIMIT = 10
MAX_SEARCH_LIMIT = 50

SQLITE_TIMEOUT_SECONDS = 10


# a persistant memory store for long-term user memory
class MemoryStore:
	def __init__(self, db_path = DB_PATH):
		self.db_path = Path(db_path).resolve()
		self.db_path.parent.mkdir(parents = True,
								exist_ok = True)

		self.initialise()


	# for connection management -> short-lived
	@contextmanager
	def connect(self):
		conn = sqlite3.connect(self.db_path,
								timeout = SQLITE_TIMEOUT_SECONDS)

		conn.row_factory = sqlite3.Row 
		
		try:
			yield conn 
			conn.commit()

		except Exception:
			conn.rollback()
			raise

		finally:
			conn.close()


	def initialise(self):
		with self.connect() as conn:
			conn.execute(f"""
						CREATE TABLE IF NOT EXISTS memory (
							id INTEGER PRIMARY KEY AUTOINCREMENT,
							category TEXT NOT NULL CHECK (length(category) BETWEEN 1 and {MAX_CATEGORY_LENGTH}),
							content TEXT NOT NULL CHECK (length(content) BETWEEN 1 and {MAX_CONTENT_LENGTH}),
							created_at TEXT NOT NULL,
							updated_at TEXT NOT NULL
						)
						""")

			# for recent memories within a category
			conn.execute("""
						CREATE INDEX IF NOT EXISTS idx_memory_category_updated
						ON memory(category, updated_at DESC, id DESC)
						""")
			# for most recently updated memories
			conn.execute("""
						CREATE INDEX IF NOT EXISTS idx_memory_updated
						ON memory(updated_at DESC, id DESC)
						""")


	# to save a new memory
	def save(self, category, content):
		category = category.strip().lower()
		content = content.strip()

		if not category or not content:
			raise ValueError("category and content can't be empty")

		if len(category) > MAX_CATEGORY_LENGTH or len(content) > MAX_CONTENT_LENGTH:
			raise ValueError("memory exceeds the size thresholds")

		now = datetime.now().isoformat()

		with self.connect() as conn:
			cursor = conn.execute("""
								INSERT INTO memory (
									category,
									content,
									created_at,
									updated_at
								)
								VALUES (?, ?, ?, ?)
								""", 
								(category, content, now, now))

			return cursor.lastrowid


	# # search memory by content/category -> simple DB search
	# def search(self, query = None, limit = DEFAULT_SEARCH_LIMIT, category = None):
	# 	if not 1 <= limit <= MAX_SEARCH_LIMIT:
	# 		raise ValueError(f"limit must be between 1 and {MAX_SEARCH_LIMIT}")

	# 	conditions = []
	# 	params = []

	# 	if query is not None:
	# 		query = query.strip()
	# 		conditions.append("content LIKE ?")
	# 		params.append(f"%{query}%")

	# 	if category is not None:
	# 		category = category.strip().lower()
	# 		conditions.append("category = ?")
	# 		params.append(category)

	# 	sql = "SELECT * FROM memory"
	# 	if conditions:
	# 		sql += " WHERE " + " AND ".join(conditions)
	# 	sql += """
	# 			ORDER BY updated_at DESC, id DESC
	# 			LIMIT ?
	# 			"""

	# 	params.append(limit)


	# 	with self.connect() as conn:
	# 		rows = conn.execute(sql, params).fetchall()

	# 	return [dict(row) for row in rows]


	# searching my lexical retrieval method
	def search(self, query = None, limit = DEFAULT_SEARCH_LIMIT, category = None):
		if not 1 <= limit <= MAX_SEARCH_LIMIT:
			raise ValueError(f"limit must be between 1 and {MAX_SEARCH_LIMIT}")

		with self.connect() as conn:
			# query all the rows of the memories table
			rows = conn.execute("""
								SELECT *
								FROM memory
								ORDER BY updated_at DESC
								LIMIT 500
								""").fetchall()

		memories = [dict(row) for row in rows]

		# return top limit memories if no query received
		if not query or not query.strip():
			return memories[:limit]

		query_tokens = {token for token in re.findall(r"[a-zA-Z0-9_]+", query.lower())
						if len(token) > 1}

		if not query_tokens:
			return []

		scored = []

		for memory in memories:
			content = memory["content"].lower()
			category = memory["category"].lower()
			combined = f"{category} {content}"

			combined_tokens = set(re.findall(r"[a-zA-Z0-9_]+", combined))
			content_tokens = set(re.findall(r"[a-zA-Z0-9_]+", content))
			category_tokens = set(re.findall(r"[a-zA-Z0-9_]+", category))

			# reject if no token matches at all
			matched_tokens = query_tokens.intersection(combined_tokens)
			if not matched_tokens:
				continue

			# score matches in content more heavily than category matches
			content_matches = query_tokens.intersection(content_tokens)
			category_matches = query_tokens.intersection(category_tokens)
			
			# partial match with content is more rewarded than category
			score = 2 * len(content_matches) + len(category_matches)
			# full match is a bonus
			if query.lower().strip() in content:
				score += 5

			memory["relevance_score"] = score 
			scored.append(memory)

		# select top limit scorers
		scored.sort(key = lambda x: (x["relevance_score"], x["updated_at"]), reverse = True)
		return scored[:limit]


	# update an existing memory entry
	def update(self, memory_id, category = None, content = None):
		if category is None and content is None:
			raise ValueError("atleast one field must be provided for update")

		updates = []
		params = []

		if category is not None:
			category = category.strip().lower()
			updates.append("category = ?")
			params.append(category)

		if content is not None:
			content = content.strip()
			updates.append("content = ?")
			params.append(content)

		now = datetime.now().isoformat()
		updates.append("updated_at = ?")
		params.append(now)

		params.append(memory_id)

		sql = f"""
				UPDATE memory
				SET {", ".join(updates)}
				WHERE id = ?
				"""

		with self.connect() as conn:
			cursor = conn.execute(sql, params)

			return cursor.rowcount > 0


	# deleting by just memory_id
	def delete(self, memory_id):
		with self.connect() as conn:
			cursor = conn.execute("""
								DELETE FROM memory WHERE id = ?
								""",
								(memory_id,))

			return cursor.rowcount > 0


	def clear_all(self):
		with self.connect() as conn:
			cursor = conn.execute("""
									DELETE FROM memory
									""")

			return cursor.rowcount


memory_store = MemoryStore()
