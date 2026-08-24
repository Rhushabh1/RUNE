import json
import re
import sqlite3
from pathlib import Path 

import numpy as np 

from app.chunking import split_into_chunks
from app.embeddings import embedding_model


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "voice_agent.db"


class HybridRAG:
	def __init__(self):
		self.initialize()


	def connect(self):
		conn = sqlite3.connect(DB_PATH, timeout = 20)
		
		conn.row_factory = sqlite3.Row 
		return conn


	def initialize(self):
		DB_PATH.parent.mkdir(parents = True, exist_ok = True)

		with self.connect() as conn:
			conn.execute("""
						CREATE TABLE IF NOT EXISTS rag_chunks (
							id INTEGER PRIMARY KEY AUTOINCREMENT,
							source_type TEXT NOT NULL,
							source_id TEXT NOT NULL,
							chunk_index INTEGER NOT NULL,
							title TEXT NOT NULL DEFAULT '',
							content TEXT NOT NULL,
							metadata TEXT NOT NULL DEFAULT '{}',
							embedding BLOB NOT NULL,
							UNIQUE(source_type, source_id, chunk_index)
						)
						""")

			conn.execute("""
						CREATE INDEX IF NOT EXISTS idx_rag_source
						ON rag_chunks(source_type, source_id)
						""")

			conn.execute("""
						CREATE VIRTUAL TABLE IF NOT EXISTS rag_fts
						USING fts5(
									title, 
									content, 
									tokenize = 'unicode61'
									)
						""")


	# for indexing
	def index_text(self, source_type, source_id, title, text, metadata = None, chunk_size = 700, overlap = 120):
		if not source_type or not source_id:
			raise ValueError("source_type and source_id are required")

		chunks = split_into_chunks(text, chunk_size = chunk_size, overlap = overlap)

		if not chunks:
			return 0

		metadata_json = json.dumps(metadata or {})

		# generate embeddings before opening the DB transaction
		embeddings = embedding_model.embed_docs(chunks)

		with self.connect() as conn:
			existing = conn.execute("""
									SELECT id
									FROM rag_chunks
									WHERE source_type = ? AND source_id = ?
									""",
									(source_type, str(source_id))).fetchall()

			for row in existing:
				conn.execute("DELETE FROM rag_fts WHERE rowid = ?",
							(row["id"],))

			conn.execute("""
						DELETE FROM rag_chunks
						WHERE source_type = ? AND source_id = ? 
						""", (source_type, str(source_id)))

			for index, (chunk, vector) in enumerate(zip(chunks, embeddings)):
				cursor = conn.execute("""
										INSERT INTO rag_chunks (
											source_type,
											source_id,
											chunk_index,
											title,
											content,
											metadata,
											embedding
										) VALUES (?, ?, ?, ?, ?, ?, ?)
										""", 
										(source_type, str(source_id), index, title or "", chunk, metadata_json, vector.astype(np.float32).tobytes()))

				chunk_id = cursor.lastrowid

				conn.execute("""
							INSERT INTO rag_fts(rowid, title, content)
							VALUES (?, ?, ?)
							""",
							(chunk_id, title or "", chunk))

		return len(chunks)



	def delete_source(self, source_type, source_id):
		with self.connect() as conn:
			rows = conn.execute("""
								SELECT id
								FROM rag_chunks
								WHERE source_type = ? AND source_id = ?
								""",
								(source_type, str(source_id))).fetchall()

			for row in rows:
				conn.execute("DELETE FROM rag_fts WHERE rowid = ?",
							(row["id"],))

			conn.execute("""
						DELETE FROM rag_chunks
						WHERE source_type = ? AND source_id = ? 
						""",
						(source_type, str(source_id)))


	# dense retrieval
	def dense_search(self, query_vector, limit = 20, source_types = None):
		sql = "SELECT * FROM rag_chunks"
		params = []

		if source_types:
			placeholders = ",".join("?" for _ in source_types)
			sql += f" WHERE source_type IN ({placeholders})"
			params.extend(source_types)

		with self.connect() as conn:
			rows = conn.execute(sql, params).fetchall()

		results = []

		for row in rows:
			vector = np.frombuffer(row["embedding"], dtype = np.float32)

			if vector.shape != query_vector.shape:
				continue

			score = float(np.dot(query_vector, vector))

			results.append({**dict(row), "dense_score": score})

		results.sort(key = lambda x: x["dense_score"], reverse = True)

		return results[:limit]


	# FTS5/BM25 for sparse retrieval
	@staticmethod
	def _fts_query(query):
		tokens = re.findall(r"[a-zA-Z0-9_]+", query)

		# quote terms to avoid treating user input as FTS syntax
		return " OR ".join('"' + token.replace('"', '""') + '"' for token in tokens)


	# main sparse retrieval function
	def sparse_search(self, query, limit = 20, source_types = None):
		fts_query = self._fts_query(query)

		if not fts_query:
			return []

		sql = """
				SELECT c.*, bm25(rag_fts) AS sparse_score
				FROM rag_fts
				JOIN rag_chunks c ON c.id = rag_fts.rowid
				WHERE rag_fts MATCH ? 
				"""

		params = [fts_query]

		if source_types:
			placeholders = ",".join("?" for _ in source_types)
			sql += f" AND c.source_type IN ({placeholders})"
			params.extend(source_types)

		sql += " ORDER BY sparse_score LIMIT ?"
		params.append(limit)

		with self.connect() as conn:
			rows = conn.execute(sql, params).fetchall()

		return [dict(row) for row in rows]


	# RRF = reciprocal rank fusion
	# RRF combines ranks rather than raw dense/BM25 scores
	@staticmethod
	def reciprocal_rank_fusion(dense_results, sparse_results, k = 60):
		fused = {}

		for ranking, results in (("dense", dense_results), ("sparse", sparse_results)):
			for rank, item in enumerate(results, start = 1):
				chunk_id = item["id"]

				if chunk_id not in fused:
					fused[chunk_id] = {
										**item,
										"rrf_score": 0.0,
										"retrieval_sources": []
										}

				fused[chunk_id]["rrf_score"] += 1.0 / (k + rank)
				fused[chunk_id]["retrieval_sources"].append(ranking)

				if ranking == "dense":
					fused[chunk_id]["dense_score"] = item["dense_score"]

				if ranking == "sparse":
					fused[chunk_id]["sparse_score"] = item["sparse_score"]

		# return sorted(fused.values(), key = lambda x: x["rrf_score"], reverse = True)
		results = list(fused.values())

		if not results:
			return []

		max_rrf = max(item["rrf_score"] for item in results)

		for item in results:
			# cosine similarity is in [-1, 1]
			dense_score = item.get("dense_score", 0.0)
			dense_normalized = (dense_score + 1.0) / 2.0

			rrf_normalized = (item["rrf_score"] / max_rrf if max_rrf else 0.0)

			item["hybrid_score"] = (0.5 * dense_normalized + 0.5 * rrf_normalized)

		return sorted(results, key = lambda x: x["hybrid_score"], reverse = True)


	# MMR diversification
	# balance query relevance against redundancy
	# relevance is dense cosine similarity to already selected chunks
	@staticmethod
	def mmr_select(candidates, query_vector, top_k = 5, lambda_mult = 0.72):
		if not candidates:
			return []

		selected = []
		remaining = candidates.copy()

		while remaining and len(selected) < top_k:
			best_item = None
			best_score = float("-inf")

			for item in remaining:
				vector =np.frombuffer(item["embedding"], dtype = np.float32)

				# now mmr balances hybrid relevance against redundancy
				# relevance = float(np.dot(query_vector, vector))
				relevance = item.get("hybrid_score", (float(np.dot(query_vector, vector)) + 1.0) / 2.0)

				if selected:
					similarities = []

					for selected_item in selected:
						selected_vector = np.frombuffer(selected_item["embedding"], dtype = np.float32)

						similarities.append(float(np.dot(vector, selected_vector)))

					redundancy = max(similarities)

				else:
					redundancy = 0.0

				mmr_score = (lambda_mult * relevance - (1.0 - lambda_mult) * redundancy)

				if mmr_score > best_score:
					best_score = mmr_score
					best_item = item 

			if best_item is None:
				break

			best_item = dict(best_item)
			best_item["mmr_score"] = best_score

			selected.append(best_item)
			remaining.remove(next(item for item in remaining if item["id"] == best_item["id"]))

		return selected



	# full hybrid retrieval pipeline
	def retrieve(self, query, candidate_k = 20, top_k = 5, source_types = None):
		if not query or not query.strip():
			return []

		query_vector = embedding_model.embed_query(query)

		dense_results = self.dense_search(query_vector, limit = candidate_k, source_types = source_types)
		sparse_results = self.sparse_search(query, limit = candidate_k, source_types = source_types)
		fused_results = self.reciprocal_rank_fusion(dense_results, sparse_results)

		# keep a bounded candidate pool for MMR
		candidates = fused_results[:candidate_k]

		return self.mmr_select(candidates, query_vector, top_k = top_k)


	# to make index rebuilding reliable
	def clear_source_type(self, source_type):
		with self.connect() as conn:
			rows = conn.execute("""
								SELECT id
								FROM rag_chunks
								WHERE source_type = ?
								""",
								(source_type,)).fetchall()

			for row in rows:
				conn.execute("DELETE FROM rag_fts WHERE rowid = ?",
							(row["id"],))

			conn.execute("DELETE FROM rag_chunks WHERE source_type = ?",
						(source_type,))


rag = HybridRAG()