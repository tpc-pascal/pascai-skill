from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from pascai_skill.core.models import MigrationReport


class MigrationManager:
    def create_report(
        self,
        skill_id: str,
        version_from: str,
        version_to: str,
        steps: List[str],
        warnings: List[str] | None = None,
    ) -> MigrationReport:
        return MigrationReport(
            skill_id=skill_id,
            version_from=version_from,
            version_to=version_to,
            steps=steps,
            warnings=warnings or [],
            success=True,
            created_at=datetime.now(timezone.utc),
        )

    def format_markdown(self, report: MigrationReport) -> str:
        lines: List[str] = []
        lines.append(f"# Migration Report: {report.skill_id}")
        lines.append("")
        lines.append(f"**From:** v{report.version_from}")
        lines.append(f"**To:** v{report.version_to}")
        lines.append(f"**Status:** {'✅ Success' if report.success else '❌ Failed'}")
        lines.append(f"**Date:** {report.created_at.strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append("")

        if report.steps:
            lines.append("## Migration Steps")
            for i, step in enumerate(report.steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")

        if report.warnings:
            lines.append("## Warnings")
            for w in report.warnings:
                lines.append(f"- ⚠ {w}")
            lines.append("")

        return "\n".join(lines)
