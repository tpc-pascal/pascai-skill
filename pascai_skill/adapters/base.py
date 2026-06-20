from __future__ import annotations

from typing import Any, Dict, List

from pascai_skill.core.interfaces import IAdapter, ISkill


class BaseAdapter(IAdapter):
    def __init__(self, name: str) -> None:
        self._name = name
        self._skills: List[ISkill] = []

    @property
    def name(self) -> str:
        return self._name

    def load_skills(self, skills: List[ISkill]) -> None:
        self._skills = [
            s for s in skills
            if "*" in s.metadata.adapter_compat or self._name in s.metadata.adapter_compat
        ]

    def get_prompts(self) -> Dict[str, str]:
        prompts: Dict[str, str] = {}
        for skill in self._skills:
            for prompt_name in skill.list_prompts():
                prompt = skill.get_prompt(prompt_name)
                if prompt:
                    prompts[f"{skill.id}.{prompt_name}"] = prompt
        return prompts

    def get_templates(self) -> Dict[str, str]:
        templates: Dict[str, str] = {}
        for skill in self._skills:
            for template_name in skill.list_templates():
                template = skill.get_template(template_name)
                if template:
                    templates[f"{skill.id}.{template_name}"] = template
        return templates

    def generate_config(self) -> Dict[str, Any]:
        return {
            "adapter": self._name,
            "skills": [
                {"id": s.id, "name": s.name, "version": s.version}
                for s in self._skills
            ],
            "prompts": list(self.get_prompts().keys()),
            "templates": list(self.get_templates().keys()),
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        return config.get("adapter") == self._name
