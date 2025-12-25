"""LangChain adapter for Agent Skills."""

from typing import Any, Dict, List, Optional, Type

from ..models import Skill
from .base import BaseAdapter

try:
    from langchain.tools import BaseTool
    from pydantic import BaseModel, Field

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseTool = object
    BaseModel = object
    Field = lambda *args, **kwargs: None


class LangChainAdapter(BaseAdapter):
    """Adapter to integrate Agent Skills with LangChain."""

    def __init__(
        self,
        skill_paths: Optional[List[str]] = None,
        auto_load: bool = True,
    ):
        """Initialize LangChain adapter.

        Args:
            skill_paths: Paths to search for skills
            auto_load: Whether to automatically load skills

        Raises:
            ImportError: If LangChain is not installed
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is not installed. Install it with: pip install langchain"
            )

        super().__init__(skill_paths=skill_paths, auto_load=auto_load)
        self.langchain_tools: List[BaseTool] = []

    def register_skill(self, skill: Skill) -> List[BaseTool]:
        """Register a skill as LangChain tools.

        Args:
            skill: Skill to register

        Returns:
            List of LangChain BaseTool instances
        """
        tools = []

        # Register each tool in the skill
        for tool_def in skill.tools:
            langchain_tool = self._create_langchain_tool(skill, tool_def.name)
            tools.append(langchain_tool)
            self.langchain_tools.append(langchain_tool)

        return tools

    def register_all_skills(self) -> List[BaseTool]:
        """Register all loaded skills as LangChain tools.

        Returns:
            List of all LangChain tools
        """
        self.langchain_tools.clear()

        for skill in self.loaded_skills:
            self.register_skill(skill)

        return self.langchain_tools

    def as_langchain_tools(self) -> List[BaseTool]:
        """Get all skills as LangChain tools.

        Returns:
            List of LangChain BaseTool instances
        """
        if not self.langchain_tools:
            self.register_all_skills()

        return self.langchain_tools

    def _create_langchain_tool(self, skill: Skill, tool_name: str) -> BaseTool:
        """Create a LangChain tool from a skill tool.

        Args:
            skill: The skill containing the tool
            tool_name: Name of the tool

        Returns:
            LangChain BaseTool instance
        """
        tool_def = skill.get_tool(tool_name)
        if not tool_def:
            raise ValueError(f"Tool '{tool_name}' not found in skill '{skill.name}'")

        # Create a dynamic tool class
        class SkillTool(BaseTool):
            name: str = f"{skill.name}_{tool_name}"
            description: str = tool_def.description

            def _run(self, **kwargs: Any) -> Any:
                """Execute the tool."""
                result = self.client.execute_tool(skill.name, tool_name, kwargs)
                if not result.success:
                    raise Exception(result.error or "Tool execution failed")
                return result.data

            async def _arun(self, **kwargs: Any) -> Any:
                """Async execution (not implemented)."""
                raise NotImplementedError("Async execution not yet supported")

        # Create instance with reference to client
        tool = SkillTool()
        tool.client = self.client  # type: ignore
        return tool

    def get_skill_instructions(self, skill_name: str) -> str:
        """Get instructions for a skill to add to agent context.

        Args:
            skill_name: Name of the skill

        Returns:
            Skill instructions
        """
        return self.client.get_instructions(skill_name)

    def inject_skill_context(self, skill_names: Optional[List[str]] = None) -> str:
        """Get concatenated instructions from multiple skills.

        Args:
            skill_names: Names of skills to include, or None for all

        Returns:
            Combined skill instructions
        """
        if skill_names is None:
            skill_names = [skill.name for skill in self.loaded_skills]

        instructions = []
        for skill_name in skill_names:
            try:
                inst = self.client.get_instructions(skill_name)
                instructions.append(f"# Skill: {skill_name}\n\n{inst}")
            except Exception:
                continue

        return "\n\n---\n\n".join(instructions)
