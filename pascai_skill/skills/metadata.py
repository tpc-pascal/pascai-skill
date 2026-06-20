from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from pascai_skill.core.models import SkillManifest, SkillMetadata, UpstreamInfo


class SkillMetadataLoader:
    SKILL_FILE = "skill.yaml"

    @classmethod
    def load_from_dir(cls, skill_dir: Path) -> Optional[SkillManifest]:
        skill_file = skill_dir / cls.SKILL_FILE
        if not skill_file.exists():
            return None
        try:
            data = yaml.safe_load(skill_file.read_text(encoding="utf-8"))
            return cls._parse_manifest(skill_dir, data)
        except Exception:
            return None

    @classmethod
    def load_from_yaml(cls, skill_dir: Path, yaml_content: str) -> SkillManifest:
        data = yaml.safe_load(yaml_content)
        return cls._parse_manifest(skill_dir, data)

    @classmethod
    def _parse_manifest(cls, skill_dir: Path, data: Dict[str, Any]) -> SkillManifest:
        skill_data = data.get("skill", data)
        upstream_data = skill_data.get("upstream")
        upstream = None
        if upstream_data:
            upstream = UpstreamInfo(
                url=upstream_data.get("url", ""),
                branch=upstream_data.get("branch", "main"),
            )

        metadata = SkillMetadata(
            id=skill_data.get("id", skill_dir.name),
            name=skill_data.get("name", skill_dir.name),
            version=skill_data.get("version", "0.1.0"),
            description=skill_data.get("description", ""),
            author=skill_data.get("author", "pascai"),
            upstream=upstream,
            tags=skill_data.get("tags", []),
            dependencies=skill_data.get("dependencies", []),
            adapter_compat=skill_data.get("adapter_compat", ["*"]),
        )

        prompts = cls._load_dir_files(skill_dir / "prompts")
        templates = cls._load_dir_files(skill_dir / "templates")
        tools = cls._load_tools(skill_dir / "tools")
        examples = cls._load_examples(skill_dir / "examples")

        return SkillManifest(
            skill=metadata,
            prompts=prompts,
            templates=templates,
            tools=tools,
            examples=examples,
        )

    @classmethod
    def _load_dir_files(cls, dir_path: Path) -> Dict[str, str]:
        if not dir_path.exists():
            return {}
        files: Dict[str, str] = {}
        for f in sorted(dir_path.iterdir()):
            if f.is_file() and f.suffix in {".md", ".txt", ".yaml", ".json", ".jinja"}:
                files[f.stem] = f.read_text(encoding="utf-8")
        return files

    @classmethod
    def _load_tools(cls, dir_path: Path) -> List[Dict[str, Any]]:
        if not dir_path.exists():
            return []
        tools: List[Dict[str, Any]] = []
        for f in sorted(dir_path.iterdir()):
            if f.suffix in {".yaml", ".json"}:
                try:
                    data = yaml.safe_load(f.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        data["_file"] = str(f.relative_to(dir_path.parent.parent))
                        tools.append(data)
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                item["_file"] = str(f.relative_to(dir_path.parent.parent))
                                tools.append(item)
                except Exception:
                    pass
        return tools

    @classmethod
    def _load_examples(cls, dir_path: Path) -> List[str]:
        if not dir_path.exists():
            return []
        examples: List[str] = []
        for f in sorted(dir_path.iterdir()):
            if f.is_file() and f.suffix in {".md", ".txt", ".py", ".sh"}:
                examples.append(f.read_text(encoding="utf-8"))
        return examples
