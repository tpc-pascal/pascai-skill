import pytest
from datetime import datetime, timezone
from pascai_skill.core.models import (
    RuntimeConfig,
    SkillMetadata,
    SkillManifest,
    UpstreamInfo,
    SyncRecord,
    MemoryEntry,
    KnowledgeEntry,
    SkillStatus,
)


class TestSkillMetadata:
    def test_default_values(self):
        m = SkillMetadata(id="test", name="Test Skill")
        assert m.version == "0.1.0"
        assert m.status == SkillStatus.INSTALLED
        assert m.tags == []
        assert m.upstream is None

    def test_with_upstream(self):
        upstream = UpstreamInfo(url="https://github.com/example/repo")
        m = SkillMetadata(
            id="test",
            name="Test",
            upstream=upstream,
        )
        assert m.has_upstream()
        assert m.upstream.url == "https://github.com/example/repo"

    def test_has_upstream_false(self):
        m = SkillMetadata(id="test", name="Test")
        assert not m.has_upstream()

    def test_invalid_upstream_url(self):
        with pytest.raises(ValueError):
            UpstreamInfo(url="invalid-url")


class TestSyncRecord:
    def test_default_status(self):
        r = SyncRecord(skill_id="test", upstream_url="https://example.com", branch="main")
        assert r.status == "pending"

    def test_full_record(self):
        now = datetime.now(timezone.utc)
        r = SyncRecord(
            skill_id="test",
            upstream_url="https://example.com",
            branch="main",
            previous_commit="abc123",
            current_commit="def456",
            synced_at=now,
            status="updated",
            changes=["file1.py", "file2.py"],
        )
        assert r.previous_commit == "abc123"
        assert len(r.changes) == 2


class TestMemoryEntry:
    def test_default_namespace(self):
        e = MemoryEntry(key="k", value="v")
        assert e.namespace == "default"

    def test_with_tags(self):
        e = MemoryEntry(key="k", value="v", tags=["tag1", "tag2"])
        assert len(e.tags) == 2


class TestKnowledgeEntry:
    def test_auto_id(self):
        e = KnowledgeEntry(source="test", content="hello")
        assert e.id is not None

    def test_default_type(self):
        e = KnowledgeEntry(source="test", content="hello")
        assert e.content_type == "markdown"


class TestRuntimeConfig:
    def test_defaults(self):
        c = RuntimeConfig()
        assert c.name == "pascai-skill"
        assert c.version == "0.1.0"
        assert not c.auto_update
        assert len(c.adapters_enabled) == 6
