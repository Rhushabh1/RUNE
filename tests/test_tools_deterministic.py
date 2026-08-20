import app.tools as tools


def test_knowledge_search_case_insensitive_and_limited(monkeypatch, tmp_path):
    knowledge = tmp_path / "notes.md"
    knowledge.write_text("Google Cloud\nMicrosoft Azure\nGoogle Vertex AI\n", encoding="utf-8")
    monkeypatch.setattr(tools, "KNOWLEDGE_FILE", knowledge)

    result = tools.search_knowledge("gOoGlE")
    assert result["result_count"] == 2
    assert result["results"] == ["Google Cloud", "Google Vertex AI"]


def test_knowledge_search_empty_query():
    result = tools.search_knowledge("   ")
    assert result["results"] == []
    assert result["message"] == "empty or invalid search query"
