from app.conversation import (ConvState, ConversationController)


def test_normal_conversation():
	controller = ConversationController()

	controller.transition(ConvState.LISTENING)
	controller.transition(ConvState.THINKING)
	controller.transition(ConvState.SPEAKING)
	controller.transition(ConvState.LISTENING)

	assert controller.state == ConvState.LISTENING


def test_interrupted_conversation():
	controller = ConversationController()

	controller.transition(ConvState.LISTENING)
	controller.transition(ConvState.THINKING)
	controller.transition(ConvState.SPEAKING)
	controller.transition(ConvState.INTERRUPTED)
	controller.transition(ConvState.LISTENING)

	assert controller.state == ConvState.LISTENING	


def test_error_recovery():
	controller = ConversationController()

	controller.transition(ConvState.LISTENING)
	controller.transition(ConvState.THINKING)
	controller.transition(ConvState.ERROR)

	controller.recover()

	assert controller.state == ConvState.IDLE


def test_invalid_transition():
	controller = ConversationController()

	try:
		controller.transition(ConvState.SPEAKING)
		assert False, "Invalid transition was accepted"
	except ValueError:
		pass


if __name__ == "__main__":
	test_normal_conversation()
	test_interrupted_conversation()
	test_error_recovery()
	test_invalid_transition()

	print("all conversation controller tests passed")