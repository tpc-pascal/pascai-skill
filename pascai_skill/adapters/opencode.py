from __future__ import annotations

from typing import Any, Dict

from pascai_skill.adapters.base import BaseAdapter


class OpenCodeAdapter(BaseAdapter):
    def __init__(self) -> None:
        super().__init__("opencode")

    def generate_config(self) -> Dict[str, Any]:
        base = super().generate_config()
        prompts = self.get_prompts()
        base["opencode_specific"] = {
            "format": "markdown",
            "instruction_prefix": "You are opencode, an interactive CLI tool.",
            "skills_enabled": [s.name for s in self._skills],
        }
        if prompts:
            base["opencode_specific"]["custom_instructions"] = list(prompts.values())
        return base
