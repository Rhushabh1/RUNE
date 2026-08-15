from enum import Enum 
from dataclasses import dataclass 


class ConvState(str, Enum):
	IDLE = "IDLE"
	LISTENING = "LISTENING"
	THINKING = "THINKING"
	SPEAKING = "SPEAKING"
	INTERRUPTED = "INTERRUPTED"
	ERROR = "ERROR"


# conversation state management
@dataclass
class ConversationController:
	state: ConvState = ConvState.IDLE

	def transition(self, new_state: ConvState):
		allowed_transitions = {
							ConvState.IDLE: {ConvState.LISTENING, ConvState.ERROR},
							ConvState.LISTENING: {ConvState.THINKING, ConvState.IDLE, ConvState.ERROR},
							ConvState.THINKING: {ConvState.SPEAKING, ConvState.INTERRUPTED, ConvState.ERROR},
							ConvState.SPEAKING: {ConvState.LISTENING, ConvState.INTERRUPTED, ConvState.IDLE, ConvState.ERROR},
							ConvState.INTERRUPTED: {ConvState.LISTENING, ConvState.THINKING, ConvState.IDLE, ConvState.ERROR},
							ConvState.ERROR: {ConvState.IDLE, ConvState.LISTENING}
							}

		if new_state not in allowed_transitions[self.state]:
			raise ValueError(f"Invalid transition: {self.state} -> {new_state}")

		self.state = new_state

		print(f"[STATE] {self.state.value}")

