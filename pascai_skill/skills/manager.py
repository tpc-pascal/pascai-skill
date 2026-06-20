from __future__ import annotations

from typing import Dict, List

from pascai_skill.core.base_skill import BaseSkill
from pascai_skill.core.exceptions import SkillNotFoundError
from pascai_skill.core.interfaces import ISkill
from pascai_skill.core.models import SkillManifest, SkillStatus
from pascai_skill.skills.registry import SkillRegistry


class SkillManager:
    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def get_skill(self, skill_id: str) -> ISkill:
        skill = self._registry.get(skill_id)
        if skill is None:
            raise SkillNotFoundError(skill_id)
        return skill

    def list_skills(self, include_disabled: bool = False) -> List[ISkill]:
        return self._registry.list_all(include_disabled)

    def get_enabled_skills(self) -> List[ISkill]:
        return self._registry.list_enabled()

    def enable_skill(self, skill_id: str) -> None:
        skill = self.get_skill(skill_id)
        skill.enable()
        self._registry.update(skill)

    def disable_skill(self, skill_id: str) -> None:
        skill = self.get_skill(skill_id)
        skill.disable()
        self._registry.update(skill)

    def install_skill(self, manifest: SkillManifest) -> ISkill:
        skill = BaseSkill(manifest)
        self._registry.register(skill)
        return skill

    def remove_skill(self, skill_id: str) -> None:
        if not self._registry.has(skill_id):
            raise SkillNotFoundError(skill_id)
        self._registry.unregister(skill_id)

    def get_skill_status(self, skill_id: str) -> SkillStatus:
        skill = self.get_skill(skill_id)
        return skill.metadata.status

    def get_prompts_for_adapter(self, adapter_name: str) -> Dict[str, str]:
        prompts: Dict[str, str] = {}
        for skill in self.get_enabled_skills():
            if adapter_name in skill.metadata.adapter_compat or "*" in skill.metadata.adapter_compat:
                for prompt_name in skill.list_prompts():
                    prompt = skill.get_prompt(prompt_name)
                    if prompt:
                        prompts[f"{skill.id}.{prompt_name}"] = prompt
        return prompts

    def get_templates_for_adapter(self, adapter_name: str) -> Dict[str, str]:
        templates: Dict[str, str] = {}
        for skill in self.get_enabled_skills():
            if adapter_name in skill.metadata.adapter_compat or "*" in skill.metadata.adapter_compat:
                for template_name in skill.list_templates():
                    template = skill.get_template(template_name)
                    if template:
                        templates[f"{skill.id}.{template_name}"] = template
        return templates

    def skill_count(self) -> int:
        return len(self._registry.list_all(include_disabled=True))

    def search_skills(self, query: str) -> List[ISkill]:
        q = query.lower()
        results: List[ISkill] = []
        for skill in self._registry.list_all(include_disabled=True):
            if (
                q in skill.id.lower()
                or q in skill.name.lower()
                or q in skill.metadata.description.lower()
            ):
                results.append(skill)
        return results
