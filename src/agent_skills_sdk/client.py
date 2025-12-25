"""Main client for Agent Skills SDK."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .discovery import SkillDiscovery
from .exceptions import ResourceNotFoundError, SkillNotFoundError
from .executor import ToolExecutor
from .models import Skill, SkillMetadata, SkillSearchQuery, ToolExecutionResult
from .parser import SkillParser


class AgentSkillsClient:
    """Main client for discovering, loading, and executing Agent Skills."""

    def __init__(
        self,
        skill_paths: Optional[List[str | Path]] = None,
        auto_discover: bool = True,
        executor_timeout: int = 30,
        executor_sandbox: bool = True,
    ):
        """Initialize the Agent Skills client.

        Args:
            skill_paths: Custom paths to search for skills. If None, uses defaults.
            auto_discover: Whether to auto-discover skills on initialization
            executor_timeout: Default timeout for tool execution in seconds
            executor_sandbox: Whether to sandbox tool execution
        """
        # Set up skill paths
        if skill_paths is None:
            self.skill_paths = SkillDiscovery.get_default_skill_paths()
        else:
            self.skill_paths = [Path(p).expanduser().resolve() for p in skill_paths]

        # Initialize components
        self.discovery = SkillDiscovery(self.skill_paths)
        self.parser = SkillParser()
        self.executor = ToolExecutor(
            timeout=executor_timeout,
            sandbox=executor_sandbox,
        )

        # Cache
        self._skills_cache: Dict[str, Skill] = {}
        self._metadata_cache: List[SkillMetadata] = []

        # Auto-discover if requested
        if auto_discover:
            self._metadata_cache = self.discovery.discover_metadata()

    def discover_skills(self) -> List[Skill]:
        """Discover all available skills.

        Returns:
            List of discovered Skill objects
        """
        skills = self.discovery.discover_skills()

        # Update cache
        for skill in skills:
            self._skills_cache[skill.name] = skill

        return skills

    def discover_metadata(self) -> List[SkillMetadata]:
        """Discover skill metadata without loading full instructions.

        Returns:
            List of SkillMetadata objects
        """
        self._metadata_cache = self.discovery.discover_metadata()
        return self._metadata_cache

    def get_metadata(self, skill_name: str) -> SkillMetadata:
        """Get metadata for a specific skill.

        Args:
            skill_name: Name of the skill

        Returns:
            SkillMetadata object

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        # Check cache first
        if skill_name in self._skills_cache:
            return self._skills_cache[skill_name].metadata

        # Check metadata cache
        for metadata in self._metadata_cache:
            if metadata.name == skill_name:
                return metadata

        # Load the skill
        skill = self.load_skill(skill_name)
        return skill.metadata

    def load_skill(self, skill_name: str) -> Skill:
        """Load a specific skill by name.

        Args:
            skill_name: Name of the skill to load

        Returns:
            Loaded Skill object

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        # Check cache
        if skill_name in self._skills_cache:
            return self._skills_cache[skill_name]

        # Find and load the skill
        skill_path = self.discovery.find_skill_path(skill_name)
        if not skill_path:
            raise SkillNotFoundError(skill_name, [str(p) for p in self.skill_paths])

        skill = self.parser.parse(skill_path)
        self._skills_cache[skill_name] = skill
        return skill

    def get_instructions(self, skill_name: str) -> str:
        """Get the full instructions for a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            Skill instructions as markdown string

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        skill = self.load_skill(skill_name)
        return skill.instructions

    def execute_tool(
        self,
        skill_name: str,
        tool_name: str,
        input_data: Dict[str, Any],
        timeout: Optional[int] = None,
    ) -> ToolExecutionResult:
        """Execute a tool from a skill.

        Args:
            skill_name: Name of the skill
            tool_name: Name of the tool to execute
            input_data: Input data for the tool
            timeout: Optional timeout override

        Returns:
            ToolExecutionResult with execution details

        Raises:
            SkillNotFoundError: If skill doesn't exist
            ToolNotFoundError: If tool doesn't exist
            ToolExecutionError: If execution fails
        """
        skill = self.load_skill(skill_name)
        return self.executor.execute(skill, tool_name, input_data, timeout)

    def get_resource(self, skill_name: str, resource_name: str) -> bytes:
        """Get a resource from a skill.

        Args:
            skill_name: Name of the skill
            resource_name: Name of the resource

        Returns:
            Resource content as bytes

        Raises:
            SkillNotFoundError: If skill doesn't exist
            ResourceNotFoundError: If resource doesn't exist
        """
        skill = self.load_skill(skill_name)

        # Find the resource
        resource = skill.get_resource(resource_name)
        if not resource:
            raise ResourceNotFoundError(resource_name, skill_name)

        # Read and return
        if not resource.path.exists():
            raise ResourceNotFoundError(resource_name, skill_name)

        with open(resource.path, "rb") as f:
            return f.read()

    def search_skills(self, query: Optional[SkillSearchQuery] = None, **kwargs) -> List[Skill]:
        """Search for skills matching criteria.

        Args:
            query: SkillSearchQuery object, or pass kwargs directly
            **kwargs: Query parameters (query, tags, type, author)

        Returns:
            List of matching Skill objects
        """
        if query is None:
            query = SkillSearchQuery(**kwargs)

        # Get all skills (from metadata cache for efficiency)
        all_skills = []

        for metadata in self._metadata_cache:
            # Filter by type
            if query.type and metadata.type != query.type:
                continue

            # Filter by tags
            if query.tags and not any(tag in metadata.tags for tag in query.tags):
                continue

            # Filter by author
            if query.author and metadata.author != query.author:
                continue

            # Filter by query text
            if query.query:
                query_lower = query.query.lower()
                if not (
                    query_lower in metadata.name.lower()
                    or query_lower in metadata.description.lower()
                    or any(query_lower in tag.lower() for tag in metadata.tags)
                ):
                    continue

            # Load the full skill
            try:
                skill = self.load_skill(metadata.name)
                all_skills.append(skill)
            except Exception:
                continue

        return all_skills

    def list_skills(self) -> List[SkillMetadata]:
        """List all available skills (metadata only).

        Returns:
            List of SkillMetadata objects
        """
        if not self._metadata_cache:
            self._metadata_cache = self.discovery.discover_metadata()
        return self._metadata_cache

    def validate_skill(self, skill_name: str) -> tuple[bool, List[str]]:
        """Validate a skill.

        Args:
            skill_name: Name of the skill to validate

        Returns:
            Tuple of (is_valid, list of error messages)

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        skill_path = self.discovery.find_skill_path(skill_name)
        if not skill_path:
            raise SkillNotFoundError(skill_name, [str(p) for p in self.skill_paths])

        return self.parser.validate(skill_path)

    def reload_skills(self) -> None:
        """Clear cache and reload all skills."""
        self._skills_cache.clear()
        self._metadata_cache = self.discovery.discover_metadata()
