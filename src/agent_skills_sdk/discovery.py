"""Skill discovery module."""

import os
from pathlib import Path
from typing import List

from .models import Skill, SkillMetadata
from .parser import SkillParser


class SkillDiscovery:
    """Discovers Agent Skills in configured directories."""

    def __init__(self, skill_paths: List[str | Path]):
        """Initialize skill discovery.

        Args:
            skill_paths: List of paths to search for skills
        """
        self.skill_paths = [Path(p).expanduser().resolve() for p in skill_paths]
        self.parser = SkillParser()

    def discover_skills(self) -> List[Skill]:
        """Discover all skills in configured paths.

        Returns:
            List of discovered Skill objects
        """
        skills = []
        seen_names = set()

        for search_path in self.skill_paths:
            if not search_path.exists():
                continue

            # Look for skill directories (containing SKILL.md)
            for skill_dir in self._find_skill_directories(search_path):
                try:
                    skill = self.parser.parse(skill_dir)

                    # Skip duplicates (first occurrence wins)
                    if skill.name in seen_names:
                        continue

                    seen_names.add(skill.name)
                    skills.append(skill)
                except Exception:
                    # Skip invalid skills during discovery
                    continue

        return skills

    def discover_metadata(self) -> List[SkillMetadata]:
        """Discover skill metadata without loading full instructions.

        This is more efficient than discover_skills() for initial scanning.

        Returns:
            List of SkillMetadata objects
        """
        metadata_list = []
        seen_names = set()

        for search_path in self.skill_paths:
            if not search_path.exists():
                continue

            for skill_dir in self._find_skill_directories(search_path):
                try:
                    # Parse only frontmatter, not full content
                    skill = self.parser.parse(skill_dir)
                    metadata = skill.metadata

                    if metadata.name in seen_names:
                        continue

                    seen_names.add(metadata.name)
                    metadata_list.append(metadata)
                except Exception:
                    continue

        return metadata_list

    def find_skill_path(self, skill_name: str) -> Path | None:
        """Find the path to a specific skill by name.

        Args:
            skill_name: Name of the skill to find

        Returns:
            Path to the skill directory, or None if not found
        """
        for search_path in self.skill_paths:
            if not search_path.exists():
                continue

            for skill_dir in self._find_skill_directories(search_path):
                try:
                    skill = self.parser.parse(skill_dir)
                    if skill.name == skill_name:
                        return skill_dir
                except Exception:
                    continue

        return None

    def _find_skill_directories(self, search_path: Path) -> List[Path]:
        """Find all directories containing SKILL.md files.

        Args:
            search_path: Root path to search

        Returns:
            List of paths to skill directories
        """
        skill_dirs = []

        if search_path.is_file():
            # If path is directly to SKILL.md
            if search_path.name == "SKILL.md":
                skill_dirs.append(search_path.parent)
            return skill_dirs

        # Search for SKILL.md files in directory
        for root, dirs, files in os.walk(search_path):
            if "SKILL.md" in files:
                skill_dirs.append(Path(root))
                # Don't recurse into skill directories
                dirs.clear()

        return skill_dirs

    @staticmethod
    def get_default_skill_paths() -> List[Path]:
        """Get the default skill search paths.

        Returns:
            List of default paths in priority order
        """
        paths = []

        # User-level skills
        user_skills = Path.home() / ".agent-skills"
        if user_skills.exists():
            paths.append(user_skills)

        # Project-level skills
        project_skills = Path.cwd() / "skills"
        if project_skills.exists():
            paths.append(project_skills)

        # Environment variable override
        env_path = os.environ.get("AGENT_SKILLS_PATH")
        if env_path:
            for path_str in env_path.split(os.pathsep):
                path = Path(path_str).expanduser().resolve()
                if path.exists() and path not in paths:
                    paths.append(path)

        return paths
