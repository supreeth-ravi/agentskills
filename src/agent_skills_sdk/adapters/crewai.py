"""CrewAI adapter for Agent Skills."""

from typing import Any, Dict, List, Optional

from ..models import Skill
from .base import BaseAdapter

try:
    from crewai_tools import BaseTool as CrewAIBaseTool

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    CrewAIBaseTool = object


class CrewAIAdapter(BaseAdapter):
    """Adapter to integrate Agent Skills with CrewAI."""

    def __init__(
        self,
        skill_paths: Optional[List[str]] = None,
        auto_load: bool = True,
    ):
        """Initialize CrewAI adapter.

        Args:
            skill_paths: Paths to search for skills
            auto_load: Whether to automatically load skills

        Raises:
            ImportError: If CrewAI is not installed
        """
        if not CREWAI_AVAILABLE:
            raise ImportError("CrewAI is not installed. Install it with: pip install crewai")

        super().__init__(skill_paths=skill_paths, auto_load=auto_load)
        self.crewai_tools: List[CrewAIBaseTool] = []

    def register_skill(self, skill: Skill) -> List[CrewAIBaseTool]:
        """Register a skill as CrewAI tools.

        Args:
            skill: Skill to register

        Returns:
            List of CrewAI tool instances
        """
        tools = []

        # Register each tool in the skill
        for tool_def in skill.tools:
            crewai_tool = self._create_crewai_tool(skill, tool_def.name)
            tools.append(crewai_tool)
            self.crewai_tools.append(crewai_tool)

        return tools

    def register_all_skills(self) -> List[CrewAIBaseTool]:
        """Register all loaded skills as CrewAI tools.

        Returns:
            List of all CrewAI tools
        """
        self.crewai_tools.clear()

        for skill in self.loaded_skills:
            self.register_skill(skill)

        return self.crewai_tools

    def as_crewai_tools(self) -> List[CrewAIBaseTool]:
        """Get all skills as CrewAI tools.

        Returns:
            List of CrewAI tool instances
        """
        if not self.crewai_tools:
            self.register_all_skills()

        return self.crewai_tools

    def _create_crewai_tool(self, skill: Skill, tool_name: str) -> CrewAIBaseTool:
        """Create a CrewAI tool from a skill tool.

        Args:
            skill: The skill containing the tool
            tool_name: Name of the tool

        Returns:
            CrewAI tool instance
        """
        tool_def = skill.get_tool(tool_name)
        if not tool_def:
            raise ValueError(f"Tool '{tool_name}' not found in skill '{skill.name}'")

        client = self.client

        class SkillTool(CrewAIBaseTool):
            name: str = f"{skill.name}_{tool_name}"
            description: str = tool_def.description

            def _run(self, **kwargs: Any) -> Any:
                """Execute the tool."""
                result = client.execute_tool(skill.name, tool_name, kwargs)
                if not result.success:
                    return f"Error: {result.error or 'Tool execution failed'}"
                return result.data

        return SkillTool()

    def get_skill_instructions_for_agent(self, skill_names: Optional[List[str]] = None) -> str:
        """Get formatted instructions for CrewAI agent backstory or goal.

        Args:
            skill_names: Names of skills to include, or None for all

        Returns:
            Formatted skill instructions
        """
        if skill_names is None:
            skill_names = [skill.name for skill in self.loaded_skills]

        instructions = []
        for skill_name in skill_names:
            try:
                inst = self.client.get_instructions(skill_name)
                instructions.append(f"**{skill_name}**:\n{inst}")
            except Exception:
                continue

        return "\n\n".join(instructions)
