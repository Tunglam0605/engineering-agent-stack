from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

from .builtins import BuiltinCatalog
from .models import CORE_ROLES, SelectedSkill, SkillContract
from .parser import safe_join


@dataclass(frozen=True)
class LoadedSkill:
    contract: SkillContract
    body: str
    references: Dict[str, str]


class SkillCatalog:
    def __init__(self, catalog: BuiltinCatalog) -> None:
        self.catalog = catalog

    def metadata(self, skill_ids: Optional[Sequence[str]] = None) -> List[dict]:
        ids = list(skill_ids) if skill_ids is not None else sorted(self.catalog.skills)
        result = []
        for ident in ids:
            skill = self.catalog.skills.get(ident)
            if skill is None:
                raise ValueError("unknown skill: " + ident)
            result.append({
                "id": skill.id,
                "version": skill.version,
                "summary": skill.summary,
                "roles": list(skill.roles),
                "task_tags": list(skill.task_tags),
                "triggers": list(skill.triggers),
                "context_cost": skill.context_cost,
            })
        return result

    def select(
        self,
        *,
        preset_id: str,
        role: str,
        task_tags: Iterable[str] = (),
        task_text: str = "",
        max_selected: int = 3,
        context_budget: int = 6000,
        explicit_skill_ids: Sequence[str] = (),
    ) -> List[SelectedSkill]:
        if role not in CORE_ROLES:
            raise ValueError("unknown core role: " + role)
        if type(max_selected) is not int or not 1 <= max_selected <= 3:
            raise ValueError("max_selected must be an integer in [1, 3]")
        if type(context_budget) is not int or context_budget < 1:
            raise ValueError("context_budget must be a positive integer")
        preset = self.catalog.presets.get(preset_id)
        if preset is None:
            raise ValueError("unknown preset: " + preset_id)
        declared = list(preset.skills)
        explicit = list(explicit_skill_ids)
        for ident in explicit:
            if ident not in self.catalog.skills:
                raise ValueError("explicit skill is not registered: " + ident)
            if ident not in declared:
                raise ValueError("explicit skill is not part of active preset: " + ident)
        tag_set = {str(tag).casefold() for tag in task_tags if str(tag).strip()}
        text = task_text.casefold()
        candidates: List[SelectedSkill] = []
        for order, ident in enumerate(declared):
            skill = self.catalog.skills[ident]
            if role not in skill.roles:
                continue
            score = 0
            skill_tags = {tag.casefold() for tag in skill.task_tags}
            score += 3 * len(tag_set & skill_tags)
            trigger_hits = sum(1 for trigger in skill.triggers if trigger.casefold() in text)
            score += 2 * trigger_hits
            if ident in explicit:
                score += 100
            # A role-compatible skill from the active preset remains eligible even
            # without trigger evidence, but evidence-backed skills sort first.
            candidates.append(
                SelectedSkill(id=ident, score=score, preset_order=order, context_cost=skill.context_cost)
            )
        candidates.sort(key=lambda item: (-item.score, item.preset_order, item.id))
        selected: List[SelectedSkill] = []
        used = 0
        for item in candidates:
            if len(selected) >= max_selected:
                break
            if used + item.context_cost > context_budget:
                continue
            selected.append(item)
            used += item.context_cost
        missing_explicit = sorted(set(explicit) - {item.id for item in selected})
        if missing_explicit:
            raise ValueError(
                "explicit skills do not fit role/context budget: " + ", ".join(missing_explicit)
            )
        return selected

    def load_selected(self, selected: Sequence[SelectedSkill]) -> List[LoadedSkill]:
        result: List[LoadedSkill] = []
        for item in selected:
            skill = self.catalog.skills.get(item.id)
            if skill is None:
                raise ValueError("selected skill disappeared from catalog: " + item.id)
            root = self.catalog.skill_roots[skill.id]
            body_path = safe_join(root, skill.body)
            if not body_path.is_file():
                raise ValueError("skill body missing: " + skill.body)
            body = body_path.read_text(encoding="utf-8")
            references: Dict[str, str] = {}
            for relative in skill.references:
                path = safe_join(root, relative)
                if not path.is_file():
                    raise ValueError("skill reference missing: " + relative)
                references[relative] = path.read_text(encoding="utf-8")
            result.append(LoadedSkill(contract=skill, body=body, references=references))
        return result
