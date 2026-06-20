from __future__ import annotations

from typing import Dict, List, Optional

from pascai_skill.core.interfaces import ISkill


class SkillRegistry:
    _instance: Optional[SkillRegistry] = None

    def __new__(cls) -> SkillRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._skills: Dict[str, ISkill] = {}
        return cls._instance

    def register(self, skill: ISkill) -> None:
        self._skills[skill.id] = skill

    def unregister(self, skill_id: str) -> None:
        self._skills.pop(skill_id, None)

    def get(self, skill_id: str) -> Optional[ISkill]:
        return self._skills.get(skill_id)

    def has(self, skill_id: str) -> bool:
        return skill_id in self._skills

    def update(self, skill: ISkill) -> None:
        self._skills[skill.id] = skill

    def list_all(self, include_disabled: bool = False) -> List[ISkill]:
        if include_disabled:
            return list(self._skills.values())
        return [s for s in self._skills.values() if s.is_enabled()]

    def list_enabled(self) -> List[ISkill]:
        return [s for s in self._skills.values() if s.is_enabled()]

    def list_ids(self) -> List[str]:
        return list(self._skills.keys())

    def clear(self) -> None:
        self._skills.clear()
