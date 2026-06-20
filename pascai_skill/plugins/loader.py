from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import List, Optional

from pascai_skill.core.base_skill import BaseSkill
from pascai_skill.core.interfaces import IAdapter, ISkill
from pascai_skill.core.models import SkillManifest


class PluginLoader:
    def __init__(self, *extra_packages: str) -> None:
        self._extra_packages = list(extra_packages)

    def discover_skills(self, skill_dirs: List[Path]) -> List[SkillManifest]:
        from pascai_skill.skills.metadata import SkillMetadataLoader

        manifests: List[SkillManifest] = []
        for skill_dir in skill_dirs:
            if not skill_dir.exists():
                continue
            for entry in sorted(skill_dir.iterdir()):
                if entry.is_dir():
                    manifest = SkillMetadataLoader.load_from_dir(entry)
                    if manifest is not None:
                        manifests.append(manifest)
        return manifests

    def load_skill(self, manifest: SkillManifest) -> ISkill:
        return BaseSkill(manifest)

    def discover_adapters(self, package_name: str = "pascai_skill.adapters") -> List[IAdapter]:
        adapters: List[IAdapter] = []
        try:
            pkg = importlib.import_module(package_name)
            for _, module_name, _ in pkgutil.iter_modules(pkg.__path__):
                if module_name == "base" or module_name.startswith("_"):
                    continue
                try:
                    full_name = f"{package_name}.{module_name}"
                    module = importlib.import_module(full_name)
                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if (
                            issubclass(obj, IAdapter)
                            and obj is not IAdapter
                            and hasattr(obj, "name")
                        ):
                            instance = obj()
                            adapters.append(instance)
                except Exception:
                    continue
        except ImportError:
            pass
        return adapters

    def load_adapter(self, name: str) -> Optional[IAdapter]:
        adapters = self.discover_adapters()
        for adapter in adapters:
            if adapter.name == name:
                return adapter
        return None
