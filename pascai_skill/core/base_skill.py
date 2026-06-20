from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from pascai_skill.core.interfaces import ISkill
from pascai_skill.core.models import SkillManifest, SkillMetadata, SkillStatus


class BaseSkill(ISkill):
    def __init__(self, manifest: SkillManifest, base_path: Optional[Path] = None) -> None:
        self._manifest = manifest
        self._base_path = base_path or Path.cwd()

    @property
    def manifest(self) -> SkillManifest:
        return self._manifest

    @property
    def metadata(self) -> SkillMetadata:
        return self._manifest.skill

    @property
    def id(self) -> str:
        return self._manifest.skill.id

    @property
    def name(self) -> str:
        return self._manifest.skill.name

    @property
    def version(self) -> str:
        return self._manifest.skill.version

    @property
    def base_path(self) -> Path:
        return self._base_path

    def get_prompt(self, name: str) -> Optional[str]:
        return self._manifest.prompts.get(name)

    def get_template(self, name: str) -> Optional[str]:
        return self._manifest.templates.get(name)

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        for tool in self._manifest.tools:
            if tool.get("name") == name:
                return tool
        return None

    def list_prompts(self) -> List[str]:
        return list(self._manifest.prompts.keys())

    def list_templates(self) -> List[str]:
        return list(self._manifest.templates.keys())

    def list_tools(self) -> List[Dict[str, Any]]:
        return self._manifest.tools

    def list_examples(self) -> List[str]:
        return self._manifest.examples

    def enable(self) -> None:
        self._manifest.skill.status = SkillStatus.ENABLED

    def disable(self) -> None:
        self._manifest.skill.status = SkillStatus.DISABLED

    def is_enabled(self) -> bool:
        return self._manifest.skill.status in (SkillStatus.ENABLED, SkillStatus.INSTALLED)

    def validate(self) -> bool:
        return bool(self._manifest.skill.id and self._manifest.skill.name)
