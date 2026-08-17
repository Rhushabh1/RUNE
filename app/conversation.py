from enum import Enum 
from dataclasses import dataclass 
from time import monotonic


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
	state_started_at: float = 0.0


	def __post_init__(self):
		self.state_started_at = monotonic()


	def transition(self, new_state: ConvState):
		allowed = {
					ConvState.IDLE: {ConvState.LISTENING, ConvState.ERROR},
					ConvState.LISTENING: {ConvState.THINKING, ConvState.IDLE, ConvState.ERROR},
					ConvState.THINKING: {ConvState.SPEAKING, ConvState.LISTENING, ConvState.INTERRUPTED, ConvState.ERROR},
					ConvState.SPEAKING: {ConvState.LISTENING, ConvState.INTERRUPTED, ConvState.IDLE, ConvState.ERROR},
					ConvState.INTERRUPTED: {ConvState.LISTENING, ConvState.THINKING, ConvState.IDLE, ConvState.ERROR},
					ConvState.ERROR: {ConvState.IDLE}
					}

		if new_state == self.state:
			return

		if new_state not in allowed[self.state]:
			raise ValueError(f"Invalid transition: {self.state.value} -> {new_state.value}")

		# tracks how long agent spends in each state
		elapsed = monotonic() - self.state_started_at
		print(f"\n[STATE] {self.state.value} -> {new_state.value} ({elapsed:.2f} sec)")

		self.state = new_state
		self.state_started_at = monotonic()


	def recover(self):
		if self.state == ConvState.ERROR:
			self.transition(ConvState.IDLE)

