import pytest
from pathlib import Path
from pascai_skill.memory.store import MemoryStore
from pascai_skill.core.models import MemoryEntry


class TestMemoryStore:
    @pytest.mark.asyncio
    async def test_set_and_get(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.db")
        entry = MemoryEntry(key="test_key", value="test_value", namespace="ns1")
        await store.set(entry)

        result = await store.get("test_key", "ns1")
        assert result is not None
        assert result.key == "test_key"
        assert result.value == "test_value"

    @pytest.mark.asyncio
    async def test_get_not_found(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.db")
        result = await store.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_search(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.db")
        await store.set(MemoryEntry(key="k1", value="hello world", namespace="ns1"))
        await store.set(MemoryEntry(key="k2", value="goodbye world", namespace="ns1"))

        results = await store.search("hello", "ns1")
        assert len(results) == 1
        assert results[0].key == "k1"

    @pytest.mark.asyncio
    async def test_delete(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.db")
        await store.set(MemoryEntry(key="del_key", value="val", namespace="ns1"))
        assert await store.delete("del_key", "ns1")
        assert not await store.delete("del_key", "ns1")

    @pytest.mark.asyncio
    async def test_list_namespaces(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.db")
        await store.set(MemoryEntry(key="k1", value="v1", namespace="ns_a"))
        await store.set(MemoryEntry(key="k2", value="v2", namespace="ns_b"))
        namespaces = await store.list_namespaces()
        assert "ns_a" in namespaces
        assert "ns_b" in namespaces
