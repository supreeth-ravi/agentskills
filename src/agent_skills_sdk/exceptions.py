"""Exception classes for Agent Skills SDK."""


class AgentSkillsError(Exception):
    """Base exception for all Agent Skills errors."""

    pass


class SkillNotFoundError(AgentSkillsError):
    """Raised when a skill cannot be found."""

    def __init__(self, skill_name: str, search_paths: list[str] | None = None):
        self.skill_name = skill_name
        self.search_paths = search_paths or []
        message = f"Skill '{skill_name}' not found"
        if search_paths:
            message += f" in paths: {', '.join(search_paths)}"
        super().__init__(message)


class SkillValidationError(AgentSkillsError):
    """Raised when a skill fails validation."""

    def __init__(self, skill_path: str, errors: list[str]):
        self.skill_path = skill_path
        self.errors = errors
        message = f"Skill validation failed for '{skill_path}':\n" + "\n".join(
            f"  - {error}" for error in errors
        )
        super().__init__(message)


class ToolExecutionError(AgentSkillsError):
    """Raised when a tool execution fails."""

    def __init__(
        self,
        tool_name: str,
        skill_name: str,
        error_message: str,
        exit_code: int | None = None,
    ):
        self.tool_name = tool_name
        self.skill_name = skill_name
        self.exit_code = exit_code
        message = f"Tool '{tool_name}' in skill '{skill_name}' failed: {error_message}"
        if exit_code is not None:
            message += f" (exit code: {exit_code})"
        super().__init__(message)


class ResourceNotFoundError(AgentSkillsError):
    """Raised when a resource cannot be found."""

    def __init__(self, resource_name: str, skill_name: str):
        self.resource_name = resource_name
        self.skill_name = skill_name
        super().__init__(f"Resource '{resource_name}' not found in skill '{skill_name}'")


class ToolNotFoundError(AgentSkillsError):
    """Raised when a tool cannot be found."""

    def __init__(self, tool_name: str, skill_name: str):
        self.tool_name = tool_name
        self.skill_name = skill_name
        super().__init__(f"Tool '{tool_name}' not found in skill '{skill_name}'")


class SkillParseError(AgentSkillsError):
    """Raised when parsing a SKILL.md file fails."""

    def __init__(self, skill_path: str, error: str):
        self.skill_path = skill_path
        super().__init__(f"Failed to parse SKILL.md at '{skill_path}': {error}")
