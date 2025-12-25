"""Agent Skills SDK - Integration layer for Agent Skills.

This SDK provides a complete integration solution for loading and executing
Agent Skills in any Python agent framework.
"""

from .client import AgentSkillsClient
from .models import Skill, SkillMetadata, SkillType
from .exceptions import (
    AgentSkillsError,
    SkillNotFoundError,
    SkillValidationError,
    ToolExecutionError,
)

__version__ = "0.1.0"

__all__ = [
    "AgentSkillsClient",
    "Skill",
    "SkillMetadata",
    "SkillType",
    "AgentSkillsError",
    "SkillNotFoundError",
    "SkillValidationError",
    "ToolExecutionError",
]
