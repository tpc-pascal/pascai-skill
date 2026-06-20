import pytest
from pascai_skill.engine.changelog import ChangeLogGenerator
from pascai_skill.engine.migration import MigrationManager
from pascai_skill.engine.backup import BackupManager


class TestChangeLogGenerator:
    def test_generate(self):
        gen = ChangeLogGenerator()
        entry = gen.generate(
            skill_id="test",
            version_from="1.0.0",
            version_to="2.0.0",
            changes=["Added feature X", "Fixed bug Y"],
            breaking_changes=["Changed API signature"],
        )
        assert entry.skill_id == "test"
        assert entry.version_from == "1.0.0"
        assert entry.version_to == "2.0.0"
        assert len(entry.changes) == 2
        assert len(entry.breaking_changes) == 1

    def test_format_markdown(self):
        gen = ChangeLogGenerator()
        entry = gen.generate("test", "1.0", "2.0", ["change1"], ["breaking1"])
        md = gen.format_markdown(entry)
        assert "# Changelog" in md
        assert "test" in md
        assert "change1" in md
        assert "breaking1" in md


class TestMigrationManager:
    def test_create_report(self):
        mgr = MigrationManager()
        report = mgr.create_report(
            skill_id="test",
            version_from="1.0",
            version_to="2.0",
            steps=["Step 1", "Step 2"],
            warnings=["Watch out for X"],
        )
        assert report.success
        assert report.version_from == "1.0"
        assert report.version_to == "2.0"
        assert len(report.steps) == 2

    def test_format_markdown(self):
        mgr = MigrationManager()
        report = mgr.create_report("test", "1.0", "2.0", ["Step 1"])
        md = mgr.format_markdown(report)
        assert "Migration Report" in md
        assert "test" in md


class TestBackupManager:
    def test_create_and_list(self, tmp_path):
        skill_path = tmp_path / "skill"
        skill_path.mkdir()
        (skill_path / "file.txt").write_text("content")

        mgr = BackupManager(tmp_path / "backups")
        backup = mgr.create_backup(skill_path, "test_skill", "1.0.0")
        assert backup.exists()

        backups = mgr.list_backups("test_skill")
        assert len(backups) == 1

        info = mgr.get_backup_info(backup)
        assert info["filename"].startswith("test_skill")

    def test_restore(self, tmp_path):
        skill_path = tmp_path / "skill_orig"
        skill_path.mkdir()
        (skill_path / "data.txt").write_text("important data")

        mgr = BackupManager(tmp_path / "backups")
        backup = mgr.create_backup(skill_path, "test", "1.0")

        restore_path = tmp_path / "skill_restored"
        mgr.restore_backup(backup, restore_path)
        assert (restore_path / "data.txt").exists()
        assert (restore_path / "data.txt").read_text() == "important data"

    def test_delete(self, tmp_path):
        mgr = BackupManager(tmp_path / "backups")
        skill_path = tmp_path / "skill"
        skill_path.mkdir()
        (skill_path / "f.txt").write_text("x")

        backup = mgr.create_backup(skill_path, "test", "1.0")
        assert mgr.delete_backup(backup)
        assert not backup.exists()
