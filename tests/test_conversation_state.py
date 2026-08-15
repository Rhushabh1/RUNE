from app.conversation import (ConvState, ConversationController)


def main():
	controller = ConversationController()

	controller.transition(ConvState.LISTENING)
	controller.transition(ConvState.THINKING)
	controller.transition(ConvState.SPEAKING)
	controller.transition(ConvState.INTERRUPTED)
	controller.transition(ConvState.LISTENING)

	print("State transition successful")


if __name__ == "__main__":
	main()