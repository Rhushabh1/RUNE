import numpy as np 
from fastembed import TextEmbedding


MODEL_NAME = "BAAI/bge-small-en-v1.5"


# simple compact english retrieval model for prototype 
class EmbeddingModel:
	def __init__(self):
		self.model = TextEmbedding(model_name = MODEL_NAME)


	def embed_docs(self, texts):
		if not texts:
			return []

		vectors = list(self.model.embed(texts))
		return [self._normalize(vector) for vector in vectors]


	# using the same embedding space for queries and docs
	def embed_query(self, query):
		return self.embed_docs([query])[0]


	@staticmethod
	def _normalize(vector):
		vector = np.asarray(vector, dtype = np.float32)
		norm = np.linalg.norm(vector)

		if norm == 0:
			return vector 

		return vector / norm


embedding_model = EmbeddingModel()