"""Command-line interface for Agent Skills SDK."""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .client import AgentSkillsClient
from .exceptions import AgentSkillsError


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Agent Skills SDK - Manage and execute agent skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--skill-paths",
        nargs="+",
        help="Paths to search for skills",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # list command
    list_parser = subparsers.add_parser("list", help="List all available skills")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_parser.add_argument("--tags", nargs="+", help="Filter by tags")
    list_parser.add_argument("--type", help="Filter by type")

    # info command
    info_parser = subparsers.add_parser("info", help="Show detailed info about a skill")
    info_parser.add_argument("skill_name", help="Name of the skill")
    info_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a skill")
    validate_parser.add_argument("skill_name", help="Name of the skill to validate")

    # exec command
    exec_parser = subparsers.add_parser("exec", help="Execute a skill tool")
    exec_parser.add_argument("skill_name", help="Name of the skill")
    exec_parser.add_argument("tool_name", help="Name of the tool")
    exec_parser.add_argument(
        "--input", "-i", help="Input data as JSON string or @filename"
    )
    exec_parser.add_argument("--timeout", type=int, help="Execution timeout in seconds")

    # search command
    search_parser = subparsers.add_parser("search", help="Search for skills")
    search_parser.add_argument("query", nargs="?", help="Search query")
    search_parser.add_argument("--tags", nargs="+", help="Filter by tags")
    search_parser.add_argument("--type", help="Filter by type")
    search_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # to-prompt command
    prompt_parser = subparsers.add_parser(
        "to-prompt", help="Generate agent prompt from skill"
    )
    prompt_parser.add_argument("skill_name", help="Name of the skill")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        # Initialize client
        client = AgentSkillsClient(skill_paths=args.skill_paths)

        # Execute command
        if args.command == "list":
            cmd_list(client, args)
        elif args.command == "info":
            cmd_info(client, args)
        elif args.command == "validate":
            cmd_validate(client, args)
        elif args.command == "exec":
            cmd_exec(client, args)
        elif args.command == "search":
            cmd_search(client, args)
        elif args.command == "to-prompt":
            cmd_to_prompt(client, args)

    except AgentSkillsError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled", file=sys.stderr)
        sys.exit(130)


def cmd_list(client: AgentSkillsClient, args: argparse.Namespace) -> None:
    """List available skills."""
    skills = client.list_skills()

    # Filter if requested
    if args.tags or args.type:
        filtered = []
        for skill in skills:
            if args.tags and not any(tag in skill.tags for tag in args.tags):
                continue
            if args.type and skill.type != args.type:
                continue
            filtered.append(skill)
        skills = filtered

    if args.json:
        output = [
            {
                "name": s.name,
                "description": s.description,
                "version": s.version,
                "type": s.type,
                "tags": s.tags,
            }
            for s in skills
        ]
        print(json.dumps(output, indent=2))
    else:
        if not skills:
            print("No skills found")
            return

        print(f"Found {len(skills)} skill(s):\n")
        for skill in skills:
            print(f"  {skill.name}")
            print(f"    {skill.description}")
            if skill.tags:
                print(f"    Tags: {', '.join(skill.tags)}")
            print()


def cmd_info(client: AgentSkillsClient, args: argparse.Namespace) -> None:
    """Show detailed info about a skill."""
    skill = client.load_skill(args.skill_name)

    if args.json:
        output = {
            "name": skill.name,
            "description": skill.description,
            "version": skill.metadata.version,
            "author": skill.metadata.author,
            "type": skill.metadata.type,
            "tags": skill.metadata.tags,
            "tools": [
                {"name": t.name, "description": t.description, "script": str(t.script_path)}
                for t in skill.tools
            ],
            "resources": [
                {"name": r.name, "path": str(r.path), "description": r.description}
                for r in skill.resources
            ],
            "root_path": str(skill.root_path),
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Skill: {skill.name}")
        print(f"Description: {skill.description}")
        if skill.metadata.version:
            print(f"Version: {skill.metadata.version}")
        if skill.metadata.author:
            print(f"Author: {skill.metadata.author}")
        if skill.metadata.type:
            print(f"Type: {skill.metadata.type}")
        if skill.metadata.tags:
            print(f"Tags: {', '.join(skill.metadata.tags)}")

        print(f"\nTools ({len(skill.tools)}):")
        for tool in skill.tools:
            print(f"  - {tool.name}: {tool.description}")

        print(f"\nResources ({len(skill.resources)}):")
        for resource in skill.resources:
            print(f"  - {resource.name}: {resource.description or resource.path}")

        print(f"\nLocation: {skill.root_path}")


def cmd_validate(client: AgentSkillsClient, args: argparse.Namespace) -> None:
    """Validate a skill."""
    is_valid, errors = client.validate_skill(args.skill_name)

    if is_valid:
        print(f"✓ Skill '{args.skill_name}' is valid")
    else:
        print(f"✗ Skill '{args.skill_name}' has errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)


def cmd_exec(client: AgentSkillsClient, args: argparse.Namespace) -> None:
    """Execute a skill tool."""
    # Parse input
    input_data = {}
    if args.input:
        if args.input.startswith("@"):
            # Read from file
            input_file = Path(args.input[1:])
            with open(input_file) as f:
                input_data = json.load(f)
        else:
            # Parse JSON string
            input_data = json.loads(args.input)

    # Execute
    result = client.execute_tool(
        args.skill_name, args.tool_name, input_data, timeout=args.timeout
    )

    if result.success:
        print(json.dumps(result.data, indent=2))
    else:
        print(f"Error: {result.error}", file=sys.stderr)
        if result.stderr:
            print(f"\nStderr:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)


def cmd_search(client: AgentSkillsClient, args: argparse.Namespace) -> None:
    """Search for skills."""
    skills = client.search_skills(
        query=args.query,
        tags=args.tags or [],
        type=args.type,
    )

    if args.json:
        output = [
            {
                "name": s.name,
                "description": s.description,
                "tags": s.metadata.tags,
            }
            for s in skills
        ]
        print(json.dumps(output, indent=2))
    else:
        if not skills:
            print("No skills found matching criteria")
            return

        print(f"Found {len(skills)} matching skill(s):\n")
        for skill in skills:
            print(f"  {skill.name}")
            print(f"    {skill.description}")
            print()


def cmd_to_prompt(client: AgentSkillsClient, args: argparse.Namespace) -> None:
    """Generate agent prompt from skill."""
    instructions = client.get_instructions(args.skill_name)
    skill = client.load_skill(args.skill_name)

    # Generate XML-formatted prompt
    print(f"<skill name=\"{skill.name}\">")
    print(f"<description>{skill.description}</description>")
    print(f"<instructions>\n{instructions}\n</instructions>")

    if skill.tools:
        print("<tools>")
        for tool in skill.tools:
            print(f"  <tool name=\"{tool.name}\">{tool.description}</tool>")
        print("</tools>")

    print("</skill>")


if __name__ == "__main__":
    main()
