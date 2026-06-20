import pytest
from pathlib import Path
from pascai_skill.upstream.version_db import VersionDatabase
from pascai_skill.core.models import SyncRecord


class TestVersionDatabase:
    def test_add_and_get(self, tmp_path):
        db = VersionDatabase(tmp_path / "version_db.json")
        record = SyncRecord(
            skill_id="test",
            upstream_url="https://example.com",
            branch="main",
            current_commit="abc123",
        )
        db.add_record(record)
        assert db.has_skill("test")
        history = db.get_history("test")
        assert len(history) == 1

    def test_get_latest(self, tmp_path):
        db = VersionDatabase(tmp_path / "version_db.json")
        r1 = SyncRecord(skill_id="test", upstream_url="https://example.com", branch="main", current_commit="abc")
        r2 = SyncRecord(skill_id="test", upstream_url="https://example.com", branch="main", current_commit="def")
        db.add_record(r1)
        db.add_record(r2)
        latest = db.get_latest("test")
        assert latest is not None
        assert latest.current_commit == "def"

    def test_list_skills(self, tmp_path):
        db = VersionDatabase(tmp_path / "version_db.json")
        db.add_record(SyncRecord(skill_id="a", upstream_url="https://a.com", branch="main"))
        db.add_record(SyncRecord(skill_id="b", upstream_url="https://b.com", branch="main"))
        skills = db.list_skills()
        assert "a" in skills
        assert "b" in skills

    def test_persistence(self, tmp_path):
        db_path = tmp_path / "version_db.json"
        db = VersionDatabase(db_path)
        db.add_record(SyncRecord(skill_id="persist", upstream_url="https://ex.com", branch="main", current_commit="xyz"))

        db2 = VersionDatabase(db_path)
        assert db2.has_skill("persist")
        assert db2.get_latest("persist").current_commit == "xyz"
