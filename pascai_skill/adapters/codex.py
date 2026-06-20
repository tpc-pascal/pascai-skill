from __future__ import annotations

from typing import Any, Dict

from pascai_skill.adapters.base import BaseAdapter


class CodexAdapter(BaseAdapter):
    def __init__(self) -> None:
        super().__init__("codex")

    def generate_config(self) -> Dict[str, Any]:
        base = super().generate_config()
        base["codex_specific"] = {
            "format": "markdown",
            "namespace": "codex",
            "skills_enabled": [s.name for s in self._skills],
            "auto_tool_use": True,
        }
        return base
