from __future__ import annotations

from typing import Any, Dict

from pascai_skill.adapters.base import BaseAdapter


class AiderAdapter(BaseAdapter):
    def __init__(self) -> None:
        super().__init__("aider")

    def generate_config(self) -> Dict[str, Any]:
        base = super().generate_config()
        base["aider_specific"] = {
            "format": "text",
            "convention_file": "aider_conventions.md",
            "skills_enabled": [s.name for s in self._skills],
            "auto_commits": True,
        }
        return base
