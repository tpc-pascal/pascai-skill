from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from pascai_skill.core.interfaces import IKnowledgeBase
from pascai_skill.core.models import KnowledgeEntry


class KnowledgeBase(IKnowledgeBase):
    def __init__(self, storage_path: Path) -> None:
        self._storage_path = storage_path
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._index_path = storage_path / "_index.json"
        self._index: Dict[str, str] = {}
        self._load_index()

    def _load_index(self) -> None:
        if self._index_path.exists():
            self._index = json.loads(self._index_path.read_text(encoding="utf-8"))

    def _save_index(self) -> None:
        self._index_path.write_text(
            json.dumps(self._index, indent=2), encoding="utf-8"
        )

    def _entry_path(self, entry_id: str) -> Path:
        return self._storage_path / f"{entry_id}.json"

    async def store(self, entry: KnowledgeEntry) -> str:
        file_path = self._entry_path(entry.id)
        file_path.write_text(
            entry.model_dump_json(indent=2),
            encoding="utf-8",
        )
        self._index[entry.id] = entry.source
        self._save_index()
        return entry.id

    async def retrieve(self, entry_id: str) -> Optional[KnowledgeEntry]:
        file_path = self._entry_path(entry_id)
        if not file_path.exists():
            return None
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return KnowledgeEntry(**data)

    async def search(self, query: str) -> List[KnowledgeEntry]:
        results: List[KnowledgeEntry] = []
        q = query.lower()
        for entry_id in self._index:
            entry = await self.retrieve(entry_id)
            if entry and (q in entry.content.lower() or q in entry.source.lower()):
                results.append(entry)
        return results

    async def delete(self, entry_id: str) -> bool:
        file_path = self._entry_path(entry_id)
        if file_path.exists():
            file_path.unlink()
            self._index.pop(entry_id, None)
            self._save_index()
            return True
        return False

    async def list_sources(self) -> List[str]:
        return list(set(self._index.values()))
