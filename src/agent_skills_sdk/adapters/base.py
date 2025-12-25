"""Base adapter for framework integrations."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List, Optional

from ..client import AgentSkillsClient
from ..models import Skill


class BaseAdapter(ABC):
    """Base class for framework adapters."""

    def __init__(
        self,
        skill_paths: Optional[List[str | Path]] = None,
        auto_load: bool = True,
    ):
        """Initialize the adapter.

        Args:
            skill_paths: Paths to search for skills
            auto_load: Whether to automatically load skills on init
        """
        self.client = AgentSkillsClient(skill_paths=skill_paths, auto_discover=True)
        self.loaded_skills: List[Skill] = []

        if auto_load:
            self.load_all_skills()

    def load_all_skills(self) -> List[Skill]:
        """Load all available skills.

        Returns:
            List of loaded skills
        """
        self.loaded_skills = self.client.discover_skills()
        return self.loaded_skills

    def load_skill(self, skill_name: str) -> Skill:
        """Load a specific skill.

        Args:
            skill_name: Name of the skill to load

        Returns:
            Loaded Skill object
        """
        skill = self.client.load_skill(skill_name)
        if skill not in self.loaded_skills:
            self.loaded_skills.append(skill)
        return skill

    @abstractmethod
    def register_skill(self, skill: Skill) -> Any:
        """Register a skill with the framework.

        Args:
            skill: Skill to register

        Returns:
            Framework-specific registration result
        """
        pass

    @abstractmethod
    def register_all_skills(self) -> List[Any]:
        """Register all loaded skills with the framework.

        Returns:
            List of framework-specific registration results
        """
        pass
