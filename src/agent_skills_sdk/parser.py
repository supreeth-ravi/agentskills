"""Parser for SKILL.md files."""

from pathlib import Path
from typing import List

import frontmatter
from pydantic import ValidationError

from .exceptions import SkillParseError, SkillValidationError
from .models import ResourceDefinition, Skill, SkillMetadata, ToolDefinition


class SkillParser:
    """Parser for Agent Skills SKILL.md files.

    Parses skills following the official Agent Skills specification:
    - Frontmatter with metadata (name, description, etc.)
    - Markdown content with instructions
    - Optional directories: scripts/, references/, assets/
    """

    def parse(self, skill_path: Path) -> Skill:
        """Parse a SKILL.md file and return a Skill object.

        Args:
            skill_path: Path to the skill directory or SKILL.md file

        Returns:
            Parsed Skill object

        Raises:
            SkillParseError: If parsing fails
            SkillValidationError: If validation fails
        """
        # Resolve the skill directory and SKILL.md path
        if skill_path.is_dir():
            skill_dir = skill_path
            skill_md_path = skill_dir / "SKILL.md"
        else:
            skill_md_path = skill_path
            skill_dir = skill_path.parent

        if not skill_md_path.exists():
            raise SkillParseError(
                str(skill_path), f"SKILL.md not found at {skill_md_path}"
            )

        try:
            # Parse frontmatter and content
            with open(skill_md_path, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)

            # Extract and validate metadata
            try:
                metadata = SkillMetadata(**post.metadata)
            except ValidationError as e:
                errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
                raise SkillValidationError(str(skill_path), errors)

            # Extract instructions (main content)
            instructions = post.content

            # Discover tools from scripts directory if it exists
            tools = self._discover_tools(skill_dir)

            # Discover resources from references and assets directories
            resources = self._discover_resources(skill_dir)

            # Identify standard directories
            scripts_dir = skill_dir / "scripts" if (skill_dir / "scripts").exists() else None
            references_dir = (
                skill_dir / "references" if (skill_dir / "references").exists() else None
            )
            assets_dir = skill_dir / "assets" if (skill_dir / "assets").exists() else None

            return Skill(
                metadata=metadata,
                root_path=skill_dir,
                skill_md_path=skill_md_path,
                instructions=instructions,
                tools=tools,
                resources=resources,
                scripts_dir=scripts_dir,
                references_dir=references_dir,
                assets_dir=assets_dir,
            )

        except Exception as e:
            if isinstance(e, (SkillParseError, SkillValidationError)):
                raise
            raise SkillParseError(str(skill_path), str(e))

    def _discover_tools(self, skill_dir: Path) -> List[ToolDefinition]:
        """Discover executable tools in the scripts directory.

        Args:
            skill_dir: Path to the skill directory

        Returns:
            List of ToolDefinition objects
        """
        tools = []
        scripts_dir = skill_dir / "scripts"

        if not scripts_dir.exists() or not scripts_dir.is_dir():
            return tools

        # Find all executable scripts
        for script_file in scripts_dir.iterdir():
            if script_file.is_file() and script_file.suffix in ['.py', '.sh', '.js', '.rb']:
                # Use filename (without extension) as tool name
                tool_name = script_file.stem.replace('_', '-')

                tools.append(
                    ToolDefinition(
                        name=tool_name,
                        description=f"Tool: {tool_name}",
                        script_path=script_file,
                    )
                )

        return tools

    def _discover_resources(self, skill_dir: Path) -> List[ResourceDefinition]:
        """Discover resources in references and assets directories.

        Args:
            skill_dir: Path to the skill directory

        Returns:
            List of ResourceDefinition objects
        """
        resources = []

        # Check references directory
        references_dir = skill_dir / "references"
        if references_dir.exists() and references_dir.is_dir():
            for resource_file in references_dir.iterdir():
                if resource_file.is_file():
                    resources.append(
                        ResourceDefinition(
                            name=resource_file.name,
                            path=resource_file,
                            description=f"Reference: {resource_file.name}",
                        )
                    )

        # Check assets directory
        assets_dir = skill_dir / "assets"
        if assets_dir.exists() and assets_dir.is_dir():
            for resource_file in assets_dir.iterdir():
                if resource_file.is_file():
                    resources.append(
                        ResourceDefinition(
                            name=resource_file.name,
                            path=resource_file,
                            description=f"Asset: {resource_file.name}",
                        )
                    )

        return resources

    def validate(self, skill_path: Path) -> tuple[bool, List[str]]:
        """Validate a skill without fully loading it.

        Args:
            skill_path: Path to the skill directory or SKILL.md file

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        try:
            skill = self.parse(skill_path)

            # Basic validation checks
            if not skill.metadata.name:
                errors.append("Skill name is required")

            if not skill.metadata.description:
                errors.append("Skill description is required")

            # Note: We don't validate tools/resources existence since they're optional
            # Skills can be pure instructional content without scripts

        except (SkillParseError, SkillValidationError) as e:
            errors.append(str(e))

        return len(errors) == 0, errors
