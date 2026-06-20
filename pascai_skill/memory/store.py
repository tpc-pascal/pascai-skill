from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from pascai_skill.core.interfaces import IMemoryStore
from pascai_skill.core.models import MemoryEntry


class MemoryStore(IMemoryStore):
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._initialize()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self._db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _initialize(self) -> None:
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                namespace TEXT NOT NULL DEFAULT 'default',
                tags TEXT DEFAULT '[]',
                source TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                ttl_seconds INTEGER,
                PRIMARY KEY (namespace, key)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_memory_namespace ON memory(namespace)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_memory_tags ON memory(tags)"
        )
        conn.commit()

    async def set(self, entry: MemoryEntry) -> None:
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()
        tags_json = json.dumps(entry.tags)
        conn.execute(
            """INSERT OR REPLACE INTO memory
               (key, value, namespace, tags, source, created_at, updated_at, ttl_seconds)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.key,
                entry.value,
                entry.namespace,
                tags_json,
                entry.source,
                entry.created_at.isoformat(),
                now,
                entry.ttl_seconds,
            ),
        )
        conn.commit()

    async def get(self, key: str, namespace: str = "default") -> Optional[MemoryEntry]:
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM memory WHERE key = ? AND namespace = ?",
            (key, namespace),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_entry(row)

    async def search(self, query: str, namespace: str = "default") -> List[MemoryEntry]:
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM memory WHERE namespace = ? AND (value LIKE ? OR key LIKE ?)",
            (namespace, f"%{query}%", f"%{query}%"),
        )
        return [self._row_to_entry(row) for row in cursor.fetchall()]

    async def delete(self, key: str, namespace: str = "default") -> bool:
        conn = self._get_conn()
        cursor = conn.execute(
            "DELETE FROM memory WHERE key = ? AND namespace = ?",
            (key, namespace),
        )
        conn.commit()
        return cursor.rowcount > 0

    async def list_namespaces(self) -> List[str]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT DISTINCT namespace FROM memory")
        return [row["namespace"] for row in cursor.fetchall()]

    def _row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        return MemoryEntry(
            key=row["key"],
            value=row["value"],
            namespace=row["namespace"],
            tags=json.loads(row["tags"]),
            source=row["source"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            ttl_seconds=row["ttl_seconds"],
        )
