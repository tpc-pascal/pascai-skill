from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from pascai_skill.core.models import ChangeLogEntry


class ChangeLogGenerator:
    def generate(
        self,
        skill_id: str,
        version_from: str,
        version_to: str,
        changes: List[str],
        breaking_changes: List[str] | None = None,
    ) -> ChangeLogEntry:
        return ChangeLogEntry(
            skill_id=skill_id,
            version_from=version_from,
            version_to=version_to,
            changes=changes,
            breaking_changes=breaking_changes or [],
            created_at=datetime.now(timezone.utc),
        )

    def format_markdown(self, entry: ChangeLogEntry) -> str:
        lines: List[str] = []
        lines.append(f"# Changelog: {entry.skill_id}")
        lines.append("")
        parts = []
        if entry.version_from:
            parts.append(f"v{entry.version_from} →")
        parts.append(f"v{entry.version_to}")
        lines.append(f"**Version:** {' '.join(parts)}")
        lines.append(f"**Date:** {entry.created_at.strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append("")

        if entry.changes:
            lines.append("## Changes")
            for change in entry.changes:
                lines.append(f"- {change}")
            lines.append("")

        if entry.breaking_changes:
            lines.append("## Breaking Changes")
            for bc in entry.breaking_changes:
                lines.append(f"- ⚠ {bc}")
            lines.append("")

        return "\n".join(lines)

    def format_json(self, entry: ChangeLogEntry) -> str:
        import json

        return json.dumps(entry.model_dump(mode="json"), indent=2, default=str)
