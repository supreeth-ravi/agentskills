#!/usr/bin/env python3
"""Agno Framework Agent with Agent Skills."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agno.agent import Agent as Agno
from agno.models.openrouter import OpenRouter
from agent_skills_sdk.adapters import AgnoAdapter

if not os.environ.get("OPENROUTER_API_KEY"):
    print("Error: OPENROUTER_API_KEY environment variable not set.")
    print("Set it with: export OPENROUTER_API_KEY='your-key'")
    sys.exit(1)


def main():
    """Run Agno agent with Agent Skills."""
    print("Creating Agno agent with Agent Skills...\n")

    # Get skills path
    skills_path = str(Path(__file__).parent.parent.parent / "skills")

    # Create adapter - implements Agent Skills standard
    adapter = AgnoAdapter(skill_paths=[skills_path])

    # Create Agno agent
    agent = Agno(
        name="agno-assistant",
        description="An AI assistant with dynamic Agent Skills support",
        model=OpenRouter(id="anthropic/claude-3.5-sonnet")
    )

    # Attach skills - agent can now discover and load skills dynamically
    adapter.attach_to_agent(agent)

    print("Agent ready! Agent has access to skills following Agent Skills standard.")
    print("Type 'quit' to exit.\n")

    # Interactive loop
    while True:
        try:
            query = input("You: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not query:
                continue

            # Run agent
            response = agent.run(query)
            print(f"\nAgent: {response.content}\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
