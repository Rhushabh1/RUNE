import re


# char-based chunking with paragraph/sentence boundaries
def split_into_chunks(text, chunk_size = 700, overlap = 120):
	if chunk_size <= 0:
		raise ValueError("chunk_size must be positive")

	if overlap < 0 or overlap >= chunk_size:
		raise ValueError("overlap must be smaller than chunk_size")

	text = re.sub(r"\s+", " ", text).strip()

	if not text:
		return []

	if len(text) <= chunk_size:
		return [text]

	chunks = []
	start = 0

	while start < len(text):
		end = min(start + chunk_size, len(text))

		if end < len(text):
			# prefer a sentence boundary, then a word boundary
			boundary = text.rfind(". ", start, end)

			if boundary < start + chunk_size // 2:
				boundary = text.rfind(" ", start, end)

			if boundary > start:
				end = boundary + 1

		chunk = text[start : end].strip()

		if chunk:
			chunks.append(chunk)

		if end >= len(text):
			break

		start = max(end - overlap, start + 1)

	return chunks

