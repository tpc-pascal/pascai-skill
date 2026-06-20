from __future__ import annotations

from typing import Any, Dict

from pascai_skill.adapters.base import BaseAdapter


class GeminiCliAdapter(BaseAdapter):
    def __init__(self) -> None:
        super().__init__("gemini_cli")

    def generate_config(self) -> Dict[str, Any]:
        base = super().generate_config()
        base["gemini_cli_specific"] = {
            "format": "text",
            "system_instruction_file": "gemini_system.txt",
            "skills_enabled": [s.name for s in self._skills],
            "model": "gemini-2.0-flash",
        }
        return base
