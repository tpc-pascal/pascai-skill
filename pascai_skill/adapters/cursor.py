from __future__ import annotations

from typing import Any, Dict

from pascai_skill.adapters.base import BaseAdapter


class CursorAdapter(BaseAdapter):
    def __init__(self) -> None:
        super().__init__("cursor")

    def generate_config(self) -> Dict[str, Any]:
        base = super().generate_config()
        base["cursor_specific"] = {
            "format": "markdown",
            "rules_file": ".cursorrules",
            "skills_enabled": [s.name for s in self._skills],
            "tab_mode": "always",
        }
        return base
