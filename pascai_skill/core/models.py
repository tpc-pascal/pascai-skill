from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SkillStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    INSTALLED = "installed"
    ERROR = "error"
    OUTDATED = "outdated"


class AdapterName(str, Enum):
    OPENCODE = "opencode"
    CLAUDE_CODE = "claude_code"
    CURSOR = "cursor"
    AIDER = "aider"
    GEMINI_CLI = "gemini_cli"
    CODEX = "codex"


class UpstreamInfo(BaseModel):
    url: str
    branch: str = "main"
    commit_hash: Optional[str] = None
    last_sync: Optional[datetime] = None
    local_path: Optional[Path] = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("https://", "git@", "http://")):
            raise ValueError(f"Invalid upstream URL: {v}")
        return v


class SyncRecord(BaseModel):
    skill_id: str
    upstream_url: str
    branch: str
    previous_commit: Optional[str] = None
    current_commit: Optional[str] = None
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"
    changes: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class SkillMetadata(BaseModel):
    id: str
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = "pascai"
    upstream: Optional[UpstreamInfo] = None
    status: SkillStatus = SkillStatus.INSTALLED
    tags: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    adapter_compat: List[str] = Field(default_factory=lambda: ["*"])
    installed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def has_upstream(self) -> bool:
        return self.upstream is not None


class SkillManifest(BaseModel):
    skill: SkillMetadata
    prompts: Dict[str, str] = Field(default_factory=dict)
    templates: Dict[str, str] = Field(default_factory=dict)
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)
    memory_keys: List[str] = Field(default_factory=list)


class AdapterConfig(BaseModel):
    name: str
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class ChangeLogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    skill_id: str
    version_from: Optional[str] = None
    version_to: str
    changes: List[str] = Field(default_factory=list)
    breaking_changes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    applied: bool = False


class MigrationReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    skill_id: str
    version_from: str
    version_to: str
    steps: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    success: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryEntry(BaseModel):
    key: str
    value: str
    namespace: str = "default"
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: Optional[int] = None


class KnowledgeEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    content: str
    content_type: str = "markdown"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RuntimeConfig(BaseModel):
    name: str = "pascai-skill"
    version: str = "0.1.0"
    data_dir: str = "./_runtime"
    auto_update: bool = False
    update_interval_hours: int = 24
    logging_level: LogLevel = LogLevel.INFO
    skill_dirs: List[str] = Field(default_factory=lambda: ["./skills", "./_runtime/installed"])
    auto_discover_skills: bool = True
    default_skill_enabled: bool = True
    adapters_enabled: List[str] = Field(default_factory=lambda: [a.value for a in AdapterName])
    memory_store: str = "sqlite"
    memory_path: str = "./_runtime/memory.db"
    knowledge_store: str = "filesystem"
    knowledge_path: str = "./_runtime/knowledge"
    upstream_cache_dir: str = "./_runtime/upstream_cache"
    sync_on_install: bool = True
    upstream_check_interval_hours: int = 24
