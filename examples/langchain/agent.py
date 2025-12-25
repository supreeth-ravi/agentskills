#!/usr/bin/env python3
"""LangChain Agent with Agent Skills."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agent_skills_sdk.adapters import LangChainAdapter

try:
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
except ImportError:
    print("Error: LangChain not installed.")
    print("Install with: pip install langchain langchain-openai")
    sys.exit(1)

if not os.environ.get("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable not set.")
    print("Set it with: export OPENAI_API_KEY='your-key'")
    sys.exit(1)


def main():
    """Run LangChain agent with Agent Skills."""
    print("Creating LangChain agent with Agent Skills...\n")

    # Get skills path
    skills_path = str(Path(__file__).parent.parent.parent / "skills")

    # Create adapter - implements Agent Skills standard
    adapter = LangChainAdapter(skill_paths=[skills_path])

    # Get LangChain tools from adapter
    tools = adapter.get_tools()

    print(f"Loaded {len(tools)} skill management tools from Agent Skills SDK")

    # Create LLM
    llm = ChatOpenAI(model="gpt-4", temperature=0)

    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an AI assistant with access to Agent Skills. "
                   "Use the available tools to discover and load skills as needed."),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create agent
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

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

            # Run agent
            result = agent_executor.invoke({"input": query})
            print(f"\nAgent: {result['output']}\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
