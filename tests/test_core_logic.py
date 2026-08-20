import pytest

from app.conversation import ConvState, ConversationController
from app.text_chunker import TextChunker
from app.tool_executor import execute_tool


def test_conversation_normal_transition_path():
    controller = ConversationController()
    controller.transition(ConvState.LISTENING)
    controller.transition(ConvState.THINKING)
    controller.transition(ConvState.SPEAKING)
    controller.transition(ConvState.LISTENING)
    assert controller.state is ConvState.LISTENING


def test_conversation_rejects_invalid_transition():
    controller = ConversationController()
    with pytest.raises(ValueError):
        controller.transition(ConvState.SPEAKING)


def test_error_recovery_returns_to_idle():
    controller = ConversationController()
    controller.transition(ConvState.ERROR)
    controller.recover()
    assert controller.state is ConvState.IDLE


def test_chunker_emits_sentence_and_flushes_remainder():
    chunker = TextChunker(max_chars=100)
    assert chunker.feed("Hello there. How are") == ["Hello there."]
    assert chunker.flush() == ["How are"]


def test_chunker_enforces_maximum_chunk_boundary():
    chunker = TextChunker(max_chars=12)
    chunks = chunker.feed("one two three four five")
    assert chunks
    assert all(len(chunk) <= 12 for chunk in chunks)


def test_unknown_tool_returns_structured_error():
    import json
    result = json.loads(execute_tool("not_a_real_tool", {}))
    assert result["error"] == "Tool not found"


def test_tool_arguments_must_be_object():
    import json
    result = json.loads(execute_tool("get_current_time", ["unexpected"]))
    assert result["error"] == "Invalid tool arguments"


def test_time_tool_returns_expected_fields():
    import json
    result = json.loads(execute_tool("get_current_time", {}))
    assert set(result) == {"time", "date"}
    assert len(result["time"]) == 8
    assert len(result["date"]) == 10
