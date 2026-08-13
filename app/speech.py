# import pyttsx3


# # speech input & output utility
# class SpeechOutput:
# 	def __init__(self):
# 		self.engine = pyttsx3.init()
# 		# set voice properties
# 		self.engine.setProperty("rate", 180)
# 		self.engine.setProperty("volume", 1.0)

# 	# converting text to audible speech
# 	def speak(self, text):
# 		if not text or not text.strip():
# 			return 

# 		try: 
# 			self.engine.say(text)
# 			self.engine.runAndWait()

# 		except Exception as e:
# 			# failsafe
# 			print(f"Speech Error: {e}")
# 			try:
# 				self.engine.stop()
# 			except Exception:
# 				pass


import pyttsx3


# speech input & output utility
class SpeechOutput:
	def __init__(self):
		pass

	# converting text to audible speech
	def speak(self, text):
		if not text or not text.strip():
			return 

		engine = pyttsx3.init("sapi5")
		engine.setProperty("rate", 180)
		engine.setProperty("volume", 1.0)
		
		engine.say(text)
		engine.runAndWait()
		engine.stop()
		del engine