from app.memory_store import MemoryStore


def test_memory_crud_isolated_to_tmp_path(tmp_path):
    store = MemoryStore(db_path=tmp_path / "test_memory.sqlite3")
    memory_id = store.save("  Preferences  ", "  Prefers concise answers  ")
    found = store.search(query="concise", category="preferences")
    assert len(found) == 1
    assert found[0]["id"] == memory_id
    assert found[0]["category"] == "preferences"

    assert store.update(memory_id, content="Prefers concise technical explanations")
    updated = store.search(query="technical")
    assert len(updated) == 1

    assert store.delete(memory_id)
    assert store.search() == []


def test_memory_rejects_empty_and_oversized_values(tmp_path):
    import pytest
    store = MemoryStore(db_path=tmp_path / "test_memory.sqlite3")
    with pytest.raises(ValueError):
        store.save("", "some content")
    with pytest.raises(ValueError):
        store.save("category", "x" * 2001)
