from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from pascai_skill.core.models import SyncRecord, UpstreamInfo
from pascai_skill.upstream.repository import GitUpstreamRepository
from pascai_skill.upstream.version_db import VersionDatabase


class SyncManager:
    def __init__(
        self, repo: GitUpstreamRepository, version_db: VersionDatabase
    ) -> None:
        self._repo = repo
        self._version_db = version_db

    async def sync(self, upstream: UpstreamInfo, skill_id: str) -> SyncRecord:
        record = SyncRecord(
            skill_id=skill_id,
            upstream_url=upstream.url,
            branch=upstream.branch,
        )
        try:
            old_hash = upstream.commit_hash
            has_updates = await self._repo.fetch_updates(upstream)
            current_commit = await self._repo.get_current_commit(upstream)
            record.current_commit = current_commit
            record.previous_commit = old_hash

            if has_updates and old_hash and current_commit:
                changes = await self._repo.compare_commits(
                    upstream, old_hash, current_commit
                )
                record.changes = changes
                record.status = "updated"
            elif not has_updates:
                record.status = "current"

            record.synced_at = datetime.now(timezone.utc)
            upstream.commit_hash = current_commit
            upstream.last_sync = record.synced_at
        except Exception as e:
            record.status = "error"
            record.error = str(e)

        self._version_db.add_record(record)
        return record

    async def install_from_url(
        self, url: str, dest: Path, skill_id: str, branch: str = "main"
    ) -> SyncRecord:
        upstream = await self._repo.clone(url, dest, branch)
        record = SyncRecord(
            skill_id=skill_id,
            upstream_url=url,
            branch=branch,
            current_commit=upstream.commit_hash,
            status="installed",
            synced_at=datetime.now(timezone.utc),
        )
        self._version_db.add_record(record)
        return record

    async def get_changelog(
        self, upstream: UpstreamInfo, since_hash: Optional[str] = None
    ) -> List[str]:
        return await self._repo.get_changelog(upstream, since_hash)

    def get_sync_history(self, skill_id: str) -> List[SyncRecord]:
        return self._version_db.get_history(skill_id)
