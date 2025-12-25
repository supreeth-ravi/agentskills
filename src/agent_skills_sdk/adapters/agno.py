"""Agno Adapter - Dynamic skill loading for Agno framework.

This adapter provides tools that allow the agent to intelligently
discover and load skills on-demand, following the Agent Skills standard.
"""

from typing import Any, Dict, List, Optional
import json

from ..models import Skill
from ..client import AgentSkillsClient

try:
    import agno
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False


class AgnoAdapter:
    """
    Agno adapter implementing Agent Skills standard with dynamic loading.

    Provides the agent with tools to:
    1. Discover available skills (metadata only - lightweight)
    2. Load skill instructions on-demand (when needed)
    3. Execute skill tools dynamically

    This enables intelligent, token-efficient skill usage.
    """

    def __init__(
        self,
        agent: Optional[Any] = None,
        skill_paths: Optional[List[str]] = None,
    ):
        """Initialize Agno adapter.

        Args:
            agent: Agno agent instance
            skill_paths: Paths to search for skills
        """
        if not AGNO_AVAILABLE:
            raise ImportError("Agno is not installed. Install it with: pip install agno")

        self.agent = agent
        self.client = AgentSkillsClient(
            skill_paths=skill_paths or [],
            auto_discover=True  # Discover all skills
        )

        # Cache for loaded skill instructions (to avoid reloading)
        self._loaded_instructions: Dict[str, str] = {}

    def create_skill_management_tools(self) -> List[Any]:
        """
        Create tools for dynamic skill management.

        Returns:
            List of tool functions that can be added to the agent
        """
        tools = []

        # Tool 1: List available skills
        def list_available_skills() -> str:
            """
            List all available skills with their descriptions.

            Use this to see what skills are available. Each skill provides
            specific capabilities. After seeing the list, you can load
            specific skill instructions if needed.

            Returns:
                JSON string with skill names and descriptions
            """
            skills = self.client.discover_metadata()

            result = {
                "total_skills": len(skills),
                "skills": [
                    {
                        "name": s.name,
                        "description": s.description,
                        "tags": getattr(s, 'tags', [])
                    }
                    for s in skills
                ]
            }

            return json.dumps(result, indent=2)

        # Tool 2: Load skill instructions
        def load_skill_instructions(skill_name: str) -> str:
            """
            Load detailed instructions for a specific skill.

            Use this when you need to understand how to use a particular
            skill. This loads the full instructions, examples, and
            capabilities for that skill.

            Args:
                skill_name: Name of the skill to load (e.g., 'pdf', 'xlsx', 'pptx')

            Returns:
                Detailed instructions for using the skill
            """
            # Check cache first
            if skill_name in self._loaded_instructions:
                return self._loaded_instructions[skill_name]

            try:
                instructions = self.client.get_instructions(skill_name)
                self._loaded_instructions[skill_name] = instructions

                return f"# Skill: {skill_name}\n\n{instructions}"
            except Exception as e:
                return f"Error loading skill '{skill_name}': {str(e)}"

        # Tool 3: Get skill tools
        def get_skill_tools(skill_name: str) -> str:
            """
            Get information about tools available in a skill.

            Args:
                skill_name: Name of the skill

            Returns:
                JSON string with tool information
            """
            try:
                skill = self.client.load_skill(skill_name)

                tools_info = {
                    "skill_name": skill.name,
                    "total_tools": len(skill.tools),
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "script_path": str(tool.script_path.name) if tool.script_path else None
                        }
                        for tool in skill.tools
                    ]
                }

                return json.dumps(tools_info, indent=2)
            except Exception as e:
                return f"Error getting tools for '{skill_name}': {str(e)}"

        # Tool 4: Search skills by capability
        def search_skills(query: str) -> str:
            """
            Search for skills that match a query.

            Use this to find relevant skills for a specific task or capability.

            Args:
                query: Search term (e.g., 'pdf', 'spreadsheet', 'presentation')

            Returns:
                JSON string with matching skills
            """
            skills = self.client.discover_metadata()
            query_lower = query.lower()

            matching = [
                {
                    "name": s.name,
                    "description": s.description,
                    "relevance": "name" if query_lower in s.name else "description"
                }
                for s in skills
                if query_lower in s.name.lower() or query_lower in s.description.lower()
            ]

            result = {
                "query": query,
                "matches_found": len(matching),
                "skills": matching
            }

            return json.dumps(result, indent=2)

        # Set tool metadata
        list_available_skills.__name__ = "list_available_skills"
        load_skill_instructions.__name__ = "load_skill_instructions"
        get_skill_tools.__name__ = "get_skill_tools"
        search_skills.__name__ = "search_skills"

        return [
            list_available_skills,
            load_skill_instructions,
            get_skill_tools,
            search_skills
        ]

    def attach_to_agent(self, agent: Any) -> None:
        """
        Attach skill management tools to an Agno agent.

        This gives the agent the ability to discover and load skills
        dynamically based on user queries.

        Args:
            agent: Agno agent instance
        """
        self.agent = agent

        # Create and add skill management tools
        tools = self.create_skill_management_tools()

        for tool in tools:
            self.agent.add_tool(tool)

    def get_token_usage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about token usage.

        Returns:
            Dictionary with token usage information
        """
        all_skills = self.client.discover_metadata()
        loaded_count = len(self._loaded_instructions)

        # Estimate tokens
        metadata_tokens = len(all_skills) * 100  # ~100 tokens per skill metadata
        loaded_tokens = sum(
            len(inst) // 4 for inst in self._loaded_instructions.values()
        )

        return {
            "total_skills_available": len(all_skills),
            "skills_loaded": loaded_count,
            "skills_not_loaded": len(all_skills) - loaded_count,
            "estimated_metadata_tokens": metadata_tokens,
            "estimated_loaded_instruction_tokens": loaded_tokens,
            "total_tokens_used": metadata_tokens + loaded_tokens,
            "loaded_skills": list(self._loaded_instructions.keys())
        }
