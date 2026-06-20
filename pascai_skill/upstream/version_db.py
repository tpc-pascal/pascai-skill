from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from pascai_skill.core.models import SyncRecord


class VersionDatabase:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._records: Dict[str, List[SyncRecord]] = {}
        self._load()

    def _load(self) -> None:
        if self._db_path.exists():
            data = json.loads(self._db_path.read_text(encoding="utf-8"))
            for skill_id, records in data.items():
                self._records[skill_id] = [SyncRecord(**r) for r in records]

    def _save(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            skill_id: [r.model_dump(mode="json") for r in records]
            for skill_id, records in self._records.items()
        }
        self._db_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def add_record(self, record: SyncRecord) -> None:
        if record.skill_id not in self._records:
            self._records[record.skill_id] = []
        self._records[record.skill_id].append(record)
        self._save()

    def get_history(self, skill_id: str) -> List[SyncRecord]:
        return self._records.get(skill_id, [])

    def get_latest(self, skill_id: str) -> Optional[SyncRecord]:
        records = self._records.get(skill_id, [])
        return records[-1] if records else None

    def list_skills(self) -> List[str]:
        return list(self._records.keys())

    def has_skill(self, skill_id: str) -> bool:
        return skill_id in self._records

    def clear(self) -> None:
        self._records.clear()
        self._save()
