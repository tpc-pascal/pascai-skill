from __future__ import annotations

import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


class BackupManager:
    def __init__(self, backup_dir: Path) -> None:
        self._backup_dir = backup_dir
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, skill_path: Path, skill_id: str, version: str) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_name = f"{skill_id}-{version}-{timestamp}.zip"
        backup_path = self._backup_dir / backup_name

        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in skill_path.rglob("*"):
                if file_path.is_file():
                    arcname = str(file_path.relative_to(skill_path))
                    zf.write(file_path, arcname)

        return backup_path

    def restore_backup(self, backup_path: Path, target_dir: Path) -> None:
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(backup_path, "r") as zf:
            zf.extractall(str(target_dir))

    def list_backups(self, skill_id: Optional[str] = None) -> List[Path]:
        backups: List[Path] = []
        for f in sorted(self._backup_dir.iterdir(), reverse=True):
            if f.suffix == ".zip":
                if skill_id is None or f.name.startswith(skill_id):
                    backups.append(f)
        return backups

    def delete_backup(self, backup_path: Path) -> bool:
        if backup_path.exists():
            backup_path.unlink()
            return True
        return False

    def get_backup_info(self, backup_path: Path) -> dict:
        if not backup_path.exists():
            return {}
        parts = backup_path.stem.split("-")
        return {
            "path": str(backup_path),
            "filename": backup_path.name,
            "size_bytes": backup_path.stat().st_size,
            "created": datetime.fromtimestamp(
                backup_path.stat().st_mtime, tz=timezone.utc
            ),
        }
