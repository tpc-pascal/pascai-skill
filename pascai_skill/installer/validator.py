from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import List, Tuple

from pascai_skill.core.models import RuntimeConfig


class Validator:
    REQUIRED_PYTHON = (3, 11)

    def __init__(self, base_dir: Path, config: RuntimeConfig) -> None:
        self._base_dir = base_dir
        self._config = config

    def run(self) -> List[str]:
        issues: List[str] = []
        issues.extend(self._check_python_version())
        issues.extend(self._check_directories())
        issues.extend(self._check_dependencies())
        issues.extend(self._check_config())
        return issues

    def _check_python_version(self) -> List[str]:
        issues: List[str] = []
        current = sys.version_info[:2]
        if current < self.REQUIRED_PYTHON:
            issues.append(
                f"Python {'.'.join(str(x) for x in self.REQUIRED_PYTHON)}+ required, "
                f"found {'.'.join(str(x) for x in current)}"
            )
        return issues

    def _check_directories(self) -> List[str]:
        issues: List[str] = []
        for d in self._config.skill_dirs:
            path = self._base_dir / d
            if not path.exists():
                issues.append(f"Skill directory not found: {d}")
        return issues

    def _check_dependencies(self) -> List[str]:
        required = [
            "pydantic",
            "yaml",
            "rich",
            "click",
            "git",
            "httpx",
            "structlog",
        ]
        issues: List[str] = []
        for dep in required:
            spec = importlib.util.find_spec(dep.split(".")[0])
            if spec is None:
                issues.append(f"Missing dependency: {dep}")
        return issues

    def _check_config(self) -> List[str]:
        issues: List[str] = []
        if not self._config.name:
            issues.append("Runtime name is empty")
        if not self._config.version:
            issues.append("Runtime version is empty")
        return issues

    def validate_skill_dir(self, skill_path: Path) -> Tuple[bool, List[str]]:
        issues: List[str] = []
        skill_file = skill_path / "skill.yaml"
        if not skill_file.exists():
            issues.append(f"Missing skill.yaml in {skill_path}")

        prompts_dir = skill_path / "prompts"
        if not prompts_dir.exists():
            issues.append(f"Missing prompts directory in {skill_path}")

        templates_dir = skill_path / "templates"
        if not templates_dir.exists():
            issues.append(f"Missing templates directory in {skill_path}")

        return (len(issues) == 0, issues)
