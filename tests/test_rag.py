from app.rag import rag


def test_hybrid_rag():
	source_id = "rag_test_001"

	try:
		rag.index_text(source_type = "test",
						source_id = source_id,
						title = "taskforge architecture",
						text = "Taskforge is a workflow scheduling platform. It uses PostgreSQL for persistent relational storage. Redis is used for caching and coordination. Kafka handles asynchronous event delivery and messaging.",
						metadata = {
									"project": "taskforge",
									"test": True
									},
						chunk_size = 300,
						overlap = 40)

		# semantic style query -> wording differs from the source
		semantic_results = rag.retrieve("which technologies provide persistent data storage and asynchronous messaging for the workflow scheduler?",
										candidate_k = 10,
										top_k = 5,
										source_types = ["test"])

		assert semantic_results, "No semantic results returned"

		# exact technical term query -> sparse retrieval should help
		keyword_results = rag.retrieve("PostgreSQL Kafka",
										candidate_k = 10,
										top_k = 5,
										source_types = ["test"])

		assert keyword_results, "No keyword results returned"

		# check fusion metadata
		for result in keyword_results:
			assert "rrf_score" in result
			assert "hybrid_score" in result
			assert "mmr_score" in result
			assert result["source_type"] == "test"
			assert result["source_id"] == source_id

		print("Hybrid RAG tests passed")

	finally:
		rag.delete_source("test", source_id)



if __name__ == "__main__":
	test_hybrid_rag()

