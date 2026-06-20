from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from pascai_skill.core.models import (
    ChangeLogEntry,
    KnowledgeEntry,
    MemoryEntry,
    MigrationReport,
    SkillManifest,
    SkillMetadata,
    UpstreamInfo,
)


class ISkill(ABC):
    @property
    @abstractmethod
    def id(self) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    @property
    @abstractmethod
    def manifest(self) -> SkillManifest: ...

    @property
    @abstractmethod
    def metadata(self) -> SkillMetadata: ...

    @abstractmethod
    def get_prompt(self, name: str) -> Optional[str]: ...

    @abstractmethod
    def get_template(self, name: str) -> Optional[str]: ...

    @abstractmethod
    def get_tool(self, name: str) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def list_prompts(self) -> List[str]: ...

    @abstractmethod
    def list_templates(self) -> List[str]: ...

    @abstractmethod
    def list_tools(self) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def list_examples(self) -> List[str]: ...

    @abstractmethod
    def enable(self) -> None: ...

    @abstractmethod
    def disable(self) -> None: ...

    @abstractmethod
    def is_enabled(self) -> bool: ...

    @abstractmethod
    def validate(self) -> bool: ...


class IAdapter(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def load_skills(self, skills: List[ISkill]) -> None: ...

    @abstractmethod
    def get_prompts(self) -> Dict[str, str]: ...

    @abstractmethod
    def get_templates(self) -> Dict[str, str]: ...

    @abstractmethod
    def generate_config(self) -> Dict[str, Any]: ...

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool: ...


class IUpstreamRepository(ABC):
    @abstractmethod
    async def clone(self, url: str, dest: Path, branch: str = "main") -> UpstreamInfo: ...

    @abstractmethod
    async def fetch_updates(self, upstream: UpstreamInfo) -> bool: ...

    @abstractmethod
    async def get_current_commit(self, upstream: UpstreamInfo) -> Optional[str]: ...

    @abstractmethod
    async def compare_commits(
        self, upstream: UpstreamInfo, old_hash: str, new_hash: str
    ) -> List[str]: ...

    @abstractmethod
    async def get_changelog(
        self, upstream: UpstreamInfo, since_hash: Optional[str] = None
    ) -> List[str]: ...

    @abstractmethod
    async def checkout_version(self, upstream: UpstreamInfo, commit_hash: str) -> None: ...


class IMemoryStore(ABC):
    @abstractmethod
    async def set(self, entry: MemoryEntry) -> None: ...

    @abstractmethod
    async def get(self, key: str, namespace: str = "default") -> Optional[MemoryEntry]: ...

    @abstractmethod
    async def search(self, query: str, namespace: str = "default") -> List[MemoryEntry]: ...

    @abstractmethod
    async def delete(self, key: str, namespace: str = "default") -> bool: ...

    @abstractmethod
    async def list_namespaces(self) -> List[str]: ...


class IKnowledgeBase(ABC):
    @abstractmethod
    async def store(self, entry: KnowledgeEntry) -> str: ...

    @abstractmethod
    async def retrieve(self, entry_id: str) -> Optional[KnowledgeEntry]: ...

    @abstractmethod
    async def search(self, query: str) -> List[KnowledgeEntry]: ...

    @abstractmethod
    async def delete(self, entry_id: str) -> bool: ...

    @abstractmethod
    async def list_sources(self) -> List[str]: ...


class IUpdateEngine(ABC):
    @abstractmethod
    async def check_updates(self, skill_id: str) -> Optional[ChangeLogEntry]: ...

    @abstractmethod
    async def apply_update(self, skill_id: str) -> MigrationReport: ...

    @abstractmethod
    async def rollback(self, skill_id: str, version: str) -> bool: ...

    @abstractmethod
    async def get_history(self, skill_id: str) -> List[ChangeLogEntry]: ...


class IPluginLoader(Protocol):
    def discover_skills(self, skill_dirs: List[Path]) -> List[SkillManifest]: ...

    def load_skill(self, manifest: SkillManifest) -> ISkill: ...

    def discover_adapters(self) -> List[IAdapter]: ...

    def load_adapter(self, name: str) -> Optional[IAdapter]: ...
