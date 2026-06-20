from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from pascai_skill.core.models import SkillManifest
from pascai_skill.plugins.loader import PluginLoader
from pascai_skill.skills.registry import SkillRegistry


class AutoDiscovery:
    def __init__(self, registry: SkillRegistry, loader: Optional[PluginLoader] = None) -> None:
        self._registry = registry
        self._loader = loader or PluginLoader()
        self._discovered_skills: List[SkillManifest] = []

    def run(
        self, skill_dirs: List[Path], load_adapters: bool = True
    ) -> Dict[str, int]:
        result: Dict[str, int] = {"skills": 0, "adapters": 0}
        skills = self._loader.discover_skills(skill_dirs)
        self._discovered_skills = skills
        for manifest in skills:
            if not self._registry.has(manifest.skill.id):
                skill = self._loader.load_skill(manifest)
                self._registry.register(skill)
                result["skills"] += 1
        if load_adapters:
            adapters = self._loader.discover_adapters()
            for adapter in adapters:
                enabled_skills = self._registry.list_enabled()
                adapter.load_skills(enabled_skills)
            result["adapters"] = len(adapters)
        return result

    def get_discovered_manifests(self) -> List[SkillManifest]:
        return self._discovered_skills

    def refresh(self, skill_dirs: List[Path]) -> int:
        count = 0
        for manifest in self._loader.discover_skills(skill_dirs):
            existing = self._registry.get(manifest.skill.id)
            if existing is None:
                skill = self._loader.load_skill(manifest)
                self._registry.register(skill)
                count += 1
            else:
                existing._manifest = manifest
                self._registry.update(existing)
                count += 1
        return count
