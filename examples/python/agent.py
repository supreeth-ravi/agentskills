#!/usr/bin/env python3
"""Pure Python Agent - Direct SDK usage without frameworks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agent_skills_sdk import AgentSkillsClient


def main():
    """Demonstrate direct SDK usage without any agent framework."""
    print("Pure Python Agent Skills SDK Demo\n")
    print("=" * 60)

    # Get skills path
    skills_path = str(Path(__file__).parent.parent.parent / "skills")

    # Create client
    client = AgentSkillsClient(skill_paths=[skills_path], auto_discover=True)

    # 1. Discover all available skills (lightweight)
    print("\n1. DISCOVERING SKILLS (metadata only)")
    print("-" * 60)
    skills = client.discover_metadata()
    print(f"Found {len(skills)} skills following Agent Skills standard:\n")

    for skill in skills:
        print(f"  • {skill.name}: {skill.description}")

    # 2. Search for specific skills
    print("\n\n2. SEARCHING FOR PDF SKILLS")
    print("-" * 60)
    query = "pdf"
    matching = [s for s in skills if query.lower() in s.name.lower()
                or query.lower() in s.description.lower()]

    print(f"Found {len(matching)} skills matching '{query}':\n")
    for skill in matching:
        print(f"  • {skill.name}")

    # 3. Load a specific skill (progressive disclosure)
    print("\n\n3. LOADING PDF SKILL (on-demand)")
    print("-" * 60)
    if matching:
        skill_name = matching[0].name
        print(f"Loading '{skill_name}' skill instructions...")

        # This is the progressive disclosure - load only when needed
        instructions = client.get_instructions(skill_name)

        print(f"\nLoaded {len(instructions)} characters of instructions")
        print(f"Estimated tokens: ~{len(instructions) // 4}")

        # Show first 500 chars
        print(f"\nFirst 500 characters:\n")
        print(instructions[:500])
        print("...\n")

    # 4. Compare token usage
    print("\n\n4. TOKEN USAGE COMPARISON")
    print("-" * 60)

    # Calculate metadata tokens
    metadata_tokens = len(skills) * 100  # ~100 tokens per skill metadata

    # Calculate full load tokens
    full_load_tokens = 0
    for skill in skills:
        try:
            instructions = client.get_instructions(skill.name)
            full_load_tokens += len(instructions) // 4
        except:
            pass

    # Single skill load
    single_skill_tokens = len(client.get_instructions(matching[0].name)) // 4 if matching else 0

    print(f"Metadata only (all {len(skills)} skills):     ~{metadata_tokens:,} tokens")
    print(f"Load 1 skill (PDF):                   ~{metadata_tokens + single_skill_tokens:,} tokens")
    print(f"Load all {len(skills)} skills (hardcoded):    ~{full_load_tokens:,} tokens")

    savings = ((full_load_tokens - (metadata_tokens + single_skill_tokens)) / full_load_tokens * 100)
    print(f"\nProgressive disclosure savings:       ~{savings:.1f}%")

    print("\n" + "=" * 60)
    print("This is how Agent Skills SDK works under the hood!")
    print("Frameworks (Agno, LangChain, CrewAI) use this same pattern.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
