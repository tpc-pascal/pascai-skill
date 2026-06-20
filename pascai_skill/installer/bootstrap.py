from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from pascai_skill.core.models import RuntimeConfig
from pascai_skill.installer.validator import Validator
from pascai_skill.plugins.discovery import AutoDiscovery
from pascai_skill.skills.registry import SkillRegistry


class Bootstrap:
    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self._base_dir = Path(base_dir or Path.cwd()).resolve()
        self._config: Optional[RuntimeConfig] = None
        self._registry = SkillRegistry()
        self._log = logging.getLogger("pascai.bootstrap")

    def initialize(self, config_path: Optional[Path] = None) -> RuntimeConfig:
        cfg_path = config_path or self._base_dir / "config.yaml"
        if cfg_path.exists():
            raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
            self._config = RuntimeConfig(**raw.get("runtime", raw))
        else:
            self._config = RuntimeConfig()

        self._create_directories()
        self._create_default_config(cfg_path)
        return self._config

    def _create_directories(self) -> None:
        dirs = [
            self._base_dir / self._config.data_dir,
            self._base_dir / self._config.data_dir / "upstream_cache",
            self._base_dir / self._config.data_dir / "backups",
            self._base_dir / self._config.data_dir / "installed",
            Path(self._config.memory_path).parent,
            Path(self._config.knowledge_path),
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        self._log.info("Runtime directories created")

    def _create_default_config(self, config_path: Path) -> None:
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"runtime": self._config.model_dump()}
            config_path.write_text(
                yaml.dump(data, default_flow_style=False, sort_keys=False),
                encoding="utf-8",
            )
            self._log.info("Default config created at %s", config_path)

    def load_skills(self) -> Dict[str, int]:
        skill_dirs = [
            self._base_dir / d for d in self._config.skill_dirs
        ]
        discovery = AutoDiscovery(self._registry)
        result = discovery.run(skill_dirs)
        self._log.info(
            "Discovered %d skills and %d adapters",
            result["skills"],
            result["adapters"],
        )
        return result

    def validate_environment(self) -> List[str]:
        validator = Validator(self._base_dir, self._config)
        return validator.run()

    @property
    def config(self) -> RuntimeConfig:
        if self._config is None:
            raise RuntimeError("Bootstrap not initialized. Call initialize() first.")
        return self._config

    @property
    def registry(self) -> SkillRegistry:
        return self._registry
