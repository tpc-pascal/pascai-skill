from __future__ import annotations

from typing import Any, Dict

from pascai_skill.adapters.base import BaseAdapter


class ClaudeCodeAdapter(BaseAdapter):
    def __init__(self) -> None:
        super().__init__("claude_code")

    def generate_config(self) -> Dict[str, Any]:
        base = super().generate_config()
        base["claude_code_specific"] = {
            "format": "markdown",
            "role": "You are Claude, an AI assistant powered by Anthropic.",
            "skills_enabled": [s.name for s in self._skills],
            "prompt_caching": True,
        }
        return base
