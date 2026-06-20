from __future__ import annotations


class PascaiError(Exception):
    """Base exception for all pascai-skill errors."""


class SkillNotFoundError(PascaiError):
    def __init__(self, skill_id: str) -> None:
        self.skill_id = skill_id
        super().__init__(f"Skill not found: {skill_id}")


class AdapterNotFoundError(PascaiError):
    def __init__(self, adapter_name: str) -> None:
        self.adapter_name = adapter_name
        super().__init__(f"Adapter not found: {adapter_name}")


class UpstreamSyncError(PascaiError):
    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        super().__init__(f"Failed to sync upstream {url}: {reason}")


class UpdateError(PascaiError):
    def __init__(self, skill_id: str, reason: str) -> None:
        self.skill_id = skill_id
        super().__init__(f"Failed to update skill {skill_id}: {reason}")


class ValidationError(PascaiError):
    def __init__(self, message: str) -> None:
        super().__init__(f"Validation failed: {message}")


class PluginLoadError(PascaiError):
    def __init__(self, plugin_name: str, reason: str) -> None:
        self.plugin_name = plugin_name
        super().__init__(f"Failed to load plugin {plugin_name}: {reason}")
