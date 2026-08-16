import re


# accumulate text until a sentence or long phrase is formed
# easy to send chunked LLM tokens to piper for natural speech fragments
class TextChunker:
	def __init__(self, max_chars = 180):
		self.buffer = ""
		self.max_chars = max_chars


	# basic chunker version -> later add abbreviations, decimals, etc.
	# streaming across sentence-sized segments, not individual audio frames (sufficient for now i guess)
	def feed(self, text):
		self.buffer += text 
		chunks = []
		while self.buffer:
			# prefer sentence boundaries for chunking
			match = re.search(r'[.!?](?:["\']?)(?:\s+|$)',
							self.buffer)

			if match:
				# find end of the regex match
				end = match.end()

				# trim at regex boundary
				chunk = self.buffer[:end].strip()
				self.buffer = self.buffer[end:]

				if chunk:
					chunks.append(chunk)
				continue

			# avoid waiting indefinitely for punctuation (trim at max_chars)
			if len(self.buffer) >= self.max_chars:
				# trim before max_chars at word boundary
				split_at = self.buffer.rfind(" ", 0, self.max_chars)
				if split_at <= 0:
					split_at = self.max_chars

				chunk = self.buffer[:split_at].strip()
				self.buffer = self.buffer[split_at:].lstrip()

				if chunk:
					chunks.append(chunk)
				continue

			break
		return chunks


	# flush the buffer clean and spit out the remaining buffer
	def flush(self):
		remaining = self.buffer.strip()
		self.buffer = ""
		return [remaining] if remaining else []