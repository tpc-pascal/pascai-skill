import pytest
from pascai_skill.knowledge.base import KnowledgeBase
from pascai_skill.core.models import KnowledgeEntry


class TestKnowledgeBase:
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, tmp_path):
        kb = KnowledgeBase(tmp_path / "knowledge")
        entry = KnowledgeEntry(source="test_doc", content="# Hello World", content_type="markdown")
        entry_id = await kb.store(entry)

        retrieved = await kb.retrieve(entry_id)
        assert retrieved is not None
        assert retrieved.source == "test_doc"
        assert retrieved.content == "# Hello World"

    @pytest.mark.asyncio
    async def test_search(self, tmp_path):
        kb = KnowledgeBase(tmp_path / "knowledge")
        await kb.store(KnowledgeEntry(source="src1", content="Python is great"))
        await kb.store(KnowledgeEntry(source="src2", content="Rust is fast"))

        results = await kb.search("Python")
        assert len(results) == 1
        assert results[0].source == "src1"

    @pytest.mark.asyncio
    async def test_delete(self, tmp_path):
        kb = KnowledgeBase(tmp_path / "knowledge")
        eid = await kb.store(KnowledgeEntry(source="src", content="content"))
        assert await kb.delete(eid)
        assert not await kb.delete(eid)

    @pytest.mark.asyncio
    async def test_list_sources(self, tmp_path):
        kb = KnowledgeBase(tmp_path / "knowledge")
        await kb.store(KnowledgeEntry(source="src_a", content="a"))
        await kb.store(KnowledgeEntry(source="src_b", content="b"))
        sources = await kb.list_sources()
        assert "src_a" in sources
        assert "src_b" in sources
