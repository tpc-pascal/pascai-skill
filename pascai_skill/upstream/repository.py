from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone

from git import Repo, GitCommandError

from pascai_skill.core.interfaces import IUpstreamRepository
from pascai_skill.core.models import UpstreamInfo
from pascai_skill.core.exceptions import UpstreamSyncError


class GitUpstreamRepository(IUpstreamRepository):
    async def clone(self, url: str, dest: Path, branch: str = "main") -> UpstreamInfo:
        dest = dest.resolve()
        if dest.exists():
            shutil.rmtree(dest)
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            repo = Repo.clone_from(url, str(dest), branch=branch)
            commit_hash = str(repo.head.commit.hexsha)
            return UpstreamInfo(
                url=url,
                branch=branch,
                commit_hash=commit_hash,
                last_sync=datetime.now(timezone.utc),
                local_path=dest,
            )
        except GitCommandError as e:
            raise UpstreamSyncError(url, str(e))

    async def fetch_updates(self, upstream: UpstreamInfo) -> bool:
        if not upstream.local_path or not upstream.local_path.exists():
            raise UpstreamSyncError(upstream.url, "Local path does not exist")
        try:
            repo = Repo(str(upstream.local_path))
            origin = repo.remotes.origin
            origin.fetch()
            old_hash = upstream.commit_hash
            new_hash = str(repo.head.commit.hexsha)
            return old_hash != new_hash
        except GitCommandError as e:
            raise UpstreamSyncError(upstream.url, str(e))

    async def get_current_commit(self, upstream: UpstreamInfo) -> Optional[str]:
        if not upstream.local_path or not upstream.local_path.exists():
            return None
        try:
            repo = Repo(str(upstream.local_path))
            return str(repo.head.commit.hexsha)
        except GitCommandError:
            return None

    async def compare_commits(
        self, upstream: UpstreamInfo, old_hash: str, new_hash: str
    ) -> List[str]:
        if not upstream.local_path or not upstream.local_path.exists():
            return []
        try:
            repo = Repo(str(upstream.local_path))
            diff = repo.git.diff("--name-only", old_hash, new_hash)
            return [line.strip() for line in diff.split("\n") if line.strip()]
        except GitCommandError:
            return []

    async def get_changelog(
        self, upstream: UpstreamInfo, since_hash: Optional[str] = None
    ) -> List[str]:
        if not upstream.local_path or not upstream.local_path.exists():
            return []
        try:
            repo = Repo(str(upstream.local_path))
            if since_hash:
                log = repo.git.log("--oneline", f"{since_hash}..HEAD")
            else:
                log = repo.git.log("--oneline", "-20")
            return [line.strip() for line in log.split("\n") if line.strip()]
        except GitCommandError:
            return []

    async def checkout_version(self, upstream: UpstreamInfo, commit_hash: str) -> None:
        if not upstream.local_path or not upstream.local_path.exists():
            raise UpstreamSyncError(upstream.url, "Local path does not exist")
        try:
            repo = Repo(str(upstream.local_path))
            repo.git.checkout(commit_hash)
            upstream.commit_hash = commit_hash
        except GitCommandError as e:
            raise UpstreamSyncError(upstream.url, str(e))
