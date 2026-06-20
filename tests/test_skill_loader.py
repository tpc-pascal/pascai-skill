import pytest
from pathlib import Path
from pascai_skill.skills.metadata import SkillMetadataLoader
from pascai_skill.skills.registry import SkillRegistry
from pascai_skill.core.base_skill import BaseSkill
from pascai_skill.core.models import SkillManifest, SkillMetadata


class TestSkillMetadataLoader:
    def test_load_from_yaml(self, tmp_path):
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()
        (skill_dir / "prompts").mkdir()
        (skill_dir / "templates").mkdir()
        (skill_dir / "prompts" / "main.md").write_text("# Main prompt")

        yaml_content = """
skill:
  id: test_skill
  name: Test Skill
  version: 1.0.0
  description: A test skill
  tags: [test]
"""
        manifest = SkillMetadataLoader.load_from_yaml(skill_dir, yaml_content)
        assert manifest.skill.id == "test_skill"
        assert manifest.skill.name == "Test Skill"
        assert manifest.skill.version == "1.0.0"
        assert "test" in manifest.skill.tags
        assert "main" in manifest.prompts

    def test_load_from_dir_not_found(self, tmp_path):
        manifest = SkillMetadataLoader.load_from_dir(tmp_path / "nonexistent")
        assert manifest is None

    def test_empty_skill_dir(self, tmp_path):
        skill_dir = tmp_path / "empty_skill"
        skill_dir.mkdir()
        (skill_dir / "skill.yaml").write_text("skill:\n  id: empty\n  name: Empty")
        manifest = SkillMetadataLoader.load_from_dir(skill_dir)
        assert manifest is not None
        assert manifest.skill.id == "empty"


class TestSkillRegistry:
    def test_singleton(self):
        r1 = SkillRegistry()
        r2 = SkillRegistry()
        assert r1 is r2

    def test_register_and_get(self):
        registry = SkillRegistry()
        registry.clear()

        manifest = SkillManifest(
            skill=SkillMetadata(id="test", name="Test", version="1.0.0"),
        )
        skill = BaseSkill(manifest)
        registry.register(skill)
        assert registry.has("test")
        assert registry.get("test") is skill

    def test_list_enabled(self):
        registry = SkillRegistry()
        registry.clear()
        assert len(registry.list_enabled()) == 0
