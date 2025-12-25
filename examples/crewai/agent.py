#!/usr/bin/env python3
"""CrewAI Agent with Agent Skills."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agent_skills_sdk.adapters import CrewAIAdapter

try:
    from crewai import Agent, Task, Crew
    from langchain_openai import ChatOpenAI
except ImportError:
    print("Error: CrewAI not installed.")
    print("Install with: pip install crewai langchain-openai")
    sys.exit(1)

if not os.environ.get("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable not set.")
    print("Set it with: export OPENAI_API_KEY='your-key'")
    sys.exit(1)


def main():
    """Run CrewAI agent with Agent Skills."""
    print("Creating CrewAI agent with Agent Skills...\n")

    # Get skills path
    skills_path = str(Path(__file__).parent.parent.parent / "skills")

    # Create adapter - implements Agent Skills standard
    adapter = CrewAIAdapter(skill_paths=[skills_path])

    # Get CrewAI tools from adapter
    tools = adapter.get_tools()

    print(f"Loaded {len(tools)} skill management tools from Agent Skills SDK")

    # Create LLM
    llm = ChatOpenAI(model="gpt-4", temperature=0)

    # Create CrewAI agent with skills
    agent = Agent(
        role="AI Assistant",
        goal="Help users with various tasks using Agent Skills",
        backstory="An AI assistant that can discover and load skills dynamically "
                  "following the Agent Skills standard.",
        tools=tools,
        llm=llm,
        verbose=True
    )

    print("\nAgent ready! Agent has access to skills following Agent Skills standard.")
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

            # Create task
            task = Task(
                description=query,
                agent=agent,
                expected_output="A helpful response to the user's question"
            )

            # Create crew and run
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=True
            )

            result = crew.kickoff()
            print(f"\nAgent: {result}\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
