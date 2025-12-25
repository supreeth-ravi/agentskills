"""Core data models for Agent Skills."""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class SkillType(str, Enum):
    """Type of skill capability."""

    WORKFLOW = "workflow"
    TOOL = "tool"
    KNOWLEDGE = "knowledge"
    DOMAIN_EXPERT = "domain-expert"


class SkillMetadata(BaseModel):
    """Metadata extracted from SKILL.md frontmatter."""

    name: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$")
    description: str = Field(..., min_length=1, max_length=1024)
    version: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    type: Optional[SkillType] = None
    tags: List[str] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)
    compatibility: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate skill name follows the spec."""
        if not v.islower():
            raise ValueError("Skill name must be lowercase")
        if not all(c.isalnum() or c == "-" for c in v):
            raise ValueError("Skill name must contain only alphanumeric characters and hyphens")
        return v


class ToolDefinition(BaseModel):
    """Definition of a skill tool."""

    name: str
    description: str
    script_path: Path
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None


class ResourceDefinition(BaseModel):
    """Definition of a skill resource."""

    name: str
    path: Path
    description: Optional[str] = None
    mime_type: Optional[str] = None


class Skill(BaseModel):
    """Complete skill definition."""

    metadata: SkillMetadata
    root_path: Path
    instructions: str
    tools: List[ToolDefinition] = Field(default_factory=list)
    resources: List[ResourceDefinition] = Field(default_factory=list)

    # Derived fields
    skill_md_path: Path
    scripts_dir: Optional[Path] = None
    references_dir: Optional[Path] = None
    assets_dir: Optional[Path] = None

    class Config:
        arbitrary_types_allowed = True

    @property
    def name(self) -> str:
        """Get skill name."""
        return self.metadata.name

    @property
    def description(self) -> str:
        """Get skill description."""
        return self.metadata.description

    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get a specific tool by name."""
        return next((t for t in self.tools if t.name == tool_name), None)

    def get_resource(self, resource_name: str) -> Optional[ResourceDefinition]:
        """Get a specific resource by name."""
        return next((r for r in self.resources if r.name == resource_name), None)


class SkillSearchQuery(BaseModel):
    """Query parameters for searching skills."""

    query: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    type: Optional[SkillType] = None
    author: Optional[str] = None


class ToolExecutionResult(BaseModel):
    """Result of a tool execution."""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time_ms: Optional[float] = None
