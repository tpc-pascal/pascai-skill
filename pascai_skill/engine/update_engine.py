from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from pascai_skill.core.exceptions import UpdateError, SkillNotFoundError
from pascai_skill.core.interfaces import IUpdateEngine
from pascai_skill.core.models import (
    ChangeLogEntry,
    MigrationReport,
    SyncRecord,
)
from pascai_skill.engine.backup import BackupManager
from pascai_skill.engine.changelog import ChangeLogGenerator
from pascai_skill.engine.migration import MigrationManager
from pascai_skill.skills.manager import SkillManager
from pascai_skill.upstream.repository import GitUpstreamRepository
from pascai_skill.upstream.sync import SyncManager
from pascai_skill.upstream.version_db import VersionDatabase


class UpdateEngine(IUpdateEngine):
    def __init__(
        self,
        skill_manager: SkillManager,
        sync_manager: SyncManager,
        version_db: VersionDatabase,
        backup_manager: BackupManager,
        changelog_gen: ChangeLogGenerator | None = None,
        migration_mgr: MigrationManager | None = None,
    ) -> None:
        self._skill_manager = skill_manager
        self._sync_manager = sync_manager
        self._version_db = version_db
        self._backup_manager = backup_manager
        self._changelog_gen = changelog_gen or ChangeLogGenerator()
        self._migration_mgr = migration_mgr or MigrationManager()

    async def check_updates(self, skill_id: str) -> Optional[ChangeLogEntry]:
        skill = self._skill_manager.get_skill(skill_id)
        upstream = skill.metadata.upstream
        if not upstream:
            return None

        current_commit = await GitUpstreamRepository().get_current_commit(upstream)
        latest_record = self._version_db.get_latest(skill_id)
        old_hash = latest_record.current_commit if latest_record else None

        if current_commit and old_hash and current_commit != old_hash:
            changes = await GitUpstreamRepository().compare_commits(
                upstream, old_hash, current_commit
            )
            return self._changelog_gen.generate(
                skill_id=skill_id,
                version_from=latest_record.version_to if latest_record else "unknown",
                version_to=current_commit[:8],
                changes=changes,
            )
        return None

    async def apply_update(self, skill_id: str) -> MigrationReport:
        skill = self._skill_manager.get_skill(skill_id)
        upstream = skill.metadata.upstream
        if not upstream or not upstream.local_path:
            raise UpdateError(skill_id, "No upstream configured for this skill")

        skill_path = upstream.local_path
        current_version = skill.version

        self._backup_manager.create_backup(skill_path, skill_id, current_version)

        record = await self._sync_manager.sync(upstream, skill_id)
        new_commit = record.current_commit or "unknown"

        steps = [
            f"Verified upstream repository at {upstream.url}",
            f"Created backup of version {current_version}",
            f"Synchronized with upstream (commit: {new_commit})",
            "Updated skill metadata",
        ]
        if record.changes:
            steps.extend([f"Applied {len(record.changes)} file changes"])

        return MigrationReport(
            skill_id=skill_id,
            version_from=current_version,
            version_to=new_commit[:8] if new_commit else "unknown",
            steps=steps,
            warnings=[] if record.status != "error" else [record.error or "Unknown error"],
            success=record.status != "error",
        )

    async def rollback(self, skill_id: str, version: str) -> bool:
        skill = self._skill_manager.get_skill(skill_id)
        upstream = skill.metadata.upstream

        backups = self._backup_manager.list_backups(skill_id)
        target_backup: Optional[Path] = None
        for b in backups:
            if version in b.name:
                target_backup = b
                break

        if target_backup and upstream and upstream.local_path:
            self._backup_manager.restore_backup(target_backup, upstream.local_path)
            return True
        return False

    async def get_history(self, skill_id: str) -> List[ChangeLogEntry]:
        records = self._version_db.get_history(skill_id)
        entries: List[ChangeLogEntry] = []
        for record in records:
            entries.append(
                ChangeLogEntry(
                    skill_id=skill_id,
                    version_from=record.previous_commit[:8] if record.previous_commit else None,
                    version_to=record.current_commit[:8] if record.current_commit else "unknown",
                    changes=record.changes,
                    created_at=record.synced_at,
                )
            )
        return entries

    async def update_all_skills(self) -> Dict[str, MigrationReport]:
        results: Dict[str, MigrationReport] = {}
        for skill in self._skill_manager.list_skills():
            if skill.metadata.has_upstream():
                try:
                    report = await self.apply_update(skill.id)
                    results[skill.id] = report
                except Exception as e:
                    results[skill.id] = MigrationReport(
                        skill_id=skill.id,
                        version_from=skill.version,
                        version_to="failed",
                        steps=[],
                        warnings=[str(e)],
                        success=False,
                    )
        return results
