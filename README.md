# Agent Skills SDK

**Implementation of [Anthropic's Agent Skills](https://agentskills.io) open standard** - makes skills discoverable and usable by agents in production frameworks.

## What is Agent Skills?

[Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) is an open standard released by Anthropic for packaging agent capabilities in a composable, portable format.

**Skills** = Organized folders with instructions, scripts, and resources that agents can discover and load dynamically.

**The Format:**
- `SKILL.md` file with YAML frontmatter (metadata)
- Progressive disclosure: Level 1 (metadata) → Level 2 (instructions) → Level 3+ (references)
- Enables agents to specialize without rebuilding entire systems

**Already in use** by Anthropic and companies in production.

## What This SDK Does

This SDK **implements the Agent Skills standard**, providing the tooling layer to make skills work in real-world applications:

- ✅ **Discovery** - Find and parse skills in Agent Skills format
- ✅ **Dynamic Loading** - Progressive disclosure (metadata first, full content on-demand)
- ✅ **Framework Integration** - Use with Agno, LangChain, CrewAI, custom frameworks
- ✅ **Token Optimization** - Load only what agents need (85-95% savings)
- ✅ **Production Ready** - Pip installable, tested, ready to deploy

## Quick Start

```bash
# Install
pip install -e .

# Set API key (for examples)
export OPENROUTER_API_KEY="your-key"

# Run examples
python examples/python/agent.py      # Pure Python (no framework)
python examples/agno/agent.py        # Agno framework
python examples/validate.py          # Token savings validation
```

## Basic Usage

```python
from agno.agent import Agent as Agno
from agno.models.openrouter import OpenRouter
from agent_skills_sdk.adapters import AgnoAdapter

# Create adapter - discovers skills in Agent Skills format
adapter = AgnoAdapter(skill_paths=["./skills"])

# Create agent
agent = Agno(
    name="assistant",
    model=OpenRouter(id="anthropic/claude-3.5-sonnet")
)

# Attach skills - agent can now discover and load them dynamically
adapter.attach_to_agent(agent)

# Use it
response = agent.run("Help me extract text from a PDF")
# Agent discovers PDF skill and loads it on-demand
```

## How It Works

The SDK provides 4 tools to agents for intelligent skill management:

1. **`list_available_skills()`** - See all available skills (metadata only, ~1600 tokens)
2. **`search_skills(query)`** - Find relevant skills by keyword
3. **`load_skill_instructions(name)`** - Load specific skill on-demand (~2000 tokens)
4. **`get_skill_tools(name)`** - Get tool information

**Progressive Disclosure in Action:**

```
User: "Can you extract text from a PDF?"
  ↓
Agent: Calls list_available_skills()
  → Sees 16 skills (metadata only: ~1600 tokens)
  ↓
Agent: Calls search_skills("pdf")
  → Finds "pdf" skill
  ↓
Agent: Calls load_skill_instructions("pdf")
  → Loads PDF instructions (~2000 tokens)
  ↓
Agent: Uses PDF skill to help user

Total: ~3600 tokens
vs Loading all 16 skills upfront: ~36,000 tokens
Savings: 90%
```

This implements the progressive disclosure pattern from the Agent Skills specification.

## Skills Included

16 skills following the Agent Skills format:

**Office Suite**
- `pdf` - PDF manipulation and text extraction
- `xlsx` - Excel spreadsheet creation and analysis
- `pptx` - PowerPoint presentation creation
- `docx` - Word document processing

**Creative**
- `canvas-design` - Visual design and graphics
- `algorithmic-art` - Generative art creation
- `theme-factory` - Theme and style generation

**Development**
- `frontend-design` - Frontend development and UI
- `webapp-testing` - Web application testing
- `web-artifacts-builder` - Build web artifacts

**Communication**
- `slack-gif-creator` - Create GIFs for Slack
- `internal-comms` - Internal communications
- `doc-coauthoring` - Collaborative document editing

**Meta**
- `skill-creator` - Create new Agent Skills
- `mcp-builder` - Build MCP servers
- `brand-guidelines` - Brand guideline management

All skills follow the [Agent Skills specification](https://agentskills.io).

## Examples

The SDK includes examples for multiple frameworks:

### Agno Framework

```bash
python examples/agno/agent.py
```

Agno agent with dynamic Agent Skills loading. Requires `OPENROUTER_API_KEY`.

### LangChain

```bash
python examples/langchain/agent.py
```

LangChain agent with Agent Skills integration. Requires `OPENAI_API_KEY` and `pip install langchain langchain-openai`.

### CrewAI

```bash
python examples/crewai/agent.py
```

CrewAI agent with Agent Skills. Requires `OPENAI_API_KEY` and `pip install crewai`.

### Pure Python (No Framework)

```bash
python examples/python/agent.py
```

Direct SDK usage without any agent framework. No API key required - demonstrates the core SDK functionality.

### Validate Token Savings

```bash
python examples/validate.py
```

See the actual token savings from progressive disclosure (84-91% reduction).

## Token Savings

Measured with real Agent Skills:

| Scenario | Tokens Used | vs All Skills | Savings |
|----------|-------------|---------------|---------|
| All 16 skills loaded upfront | 36,884 | - | 0% |
| Dynamic loading (1 skill) | 3,282 | 36,884 | **91%** |
| Dynamic loading (2 skills) | 5,805 | 36,884 | **84%** |

Progressive disclosure enables massive token savings while maintaining full capability.

## Framework Adapters

### Agno

```python
from agent_skills_sdk.adapters import AgnoAdapter

adapter = AgnoAdapter(skill_paths=["./skills"])
adapter.attach_to_agent(agent)
```

### LangChain

```python
from agent_skills_sdk.adapters import LangChainAdapter

adapter = LangChainAdapter(skill_paths=["./skills"])
tools = adapter.get_tools()
```

### CrewAI

```python
from agent_skills_sdk.adapters import CrewAIAdapter

adapter = CrewAIAdapter(skill_paths=["./skills"])
tools = adapter.get_tools()
```

## Creating Skills

Skills follow the [Agent Skills format](https://agentskills.io/specification):

```markdown
---
name: my-skill
description: What this skill does
category: utility
---

# Skill: My Skill

## Overview
Instructions for the AI agent...

## Tools Available
- tool_name: Description of the tool

## Examples
...
```

Place in: `skills/my-skill/SKILL.md`

See the [Agent Skills specification](https://agentskills.io/specification) for complete format details.

## Validation

Verify token savings with your skills:

```bash
python examples/validate.py
```

Example output:
```
✅ Discovered 16 skills
✅ Token savings: 84.3% (31,079 tokens saved)
✅ All skills loaded: ~36,884 tokens
✅ Dynamic loading: ~5,805 tokens
```

## API Reference

### AgnoAdapter

```python
from agent_skills_sdk.adapters import AgnoAdapter

adapter = AgnoAdapter(skill_paths: List[str])
adapter.attach_to_agent(agent)
adapter.get_token_usage_stats()  # Get usage statistics
```

### AgentSkillsClient

```python
from agent_skills_sdk import AgentSkillsClient

client = AgentSkillsClient(
    skill_paths: List[str],
    auto_discover: bool = True
)

# Discovery
skills = client.discover_metadata()  # Lightweight metadata only

# Loading
skill = client.load_skill(name: str)  # Load full skill
instructions = client.get_instructions(name: str)  # Instructions only

# Search
results = client.search_skills(query: str)  # Find relevant skills
```

## Project Structure

```
agentskills/
├── src/agent_skills_sdk/    # SDK implementation
│   ├── client.py             # Skills client
│   ├── discovery.py          # Skill discovery
│   ├── parser.py             # Agent Skills format parser
│   └── adapters/             # Framework adapters
│       ├── agno.py           # Agno adapter
│       ├── langchain.py      # LangChain adapter
│       └── crewai.py         # CrewAI adapter
├── skills/                   # 16 example skills (Agent Skills format)
├── examples/                 # Framework examples
│   ├── agno/agent.py         # Agno framework
│   ├── langchain/agent.py    # LangChain framework
│   ├── crewai/agent.py       # CrewAI framework
│   ├── python/agent.py       # Pure Python (no framework)
│   └── validate.py           # Token savings validation
├── tests/                    # Unit tests
└── README.md
```

## Development

```bash
# Install dependencies
pip install -e .

# Run tests
pytest tests/

# Run validation
python examples/validate.py
```

## Relationship to Agent Skills

This SDK **implements** the [Agent Skills specification](https://agentskills.io):

- **Agent Skills** (by Anthropic) = The open standard/format
- **Agent Skills SDK** (this project) = Production implementation with framework integrations

Like:
- Markdown = Format specification
- Markdown parsers = Implementations

We follow the Agent Skills specification and will evolve as the standard evolves.

## Related Resources

- [Agent Skills Announcement](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) - Anthropic's introduction
- [Agent Skills Specification](https://agentskills.io) - Official specification
- [Agent Skills Repository](https://github.com/agentskills/agentskills) - Reference implementation
- [Example Skills](https://github.com/anthropics/skills) - Community skills

## License

MIT License - See LICENSE file

## Credits

**Agent Skills Standard:** Created by [Anthropic](https://www.anthropic.com) as an open standard.

**SDK Implementation:**
- **Author:** Supreeth Ravi
- **Website:** [supreethravi.com](https://supreethravi.com)
- **LinkedIn:** [linkedin.com/in/supreeth-ravi](https://www.linkedin.com/in/supreeth-ravi/)
- **Twitter/X:** [@supreeth___ravi](https://x.com/supreeth___ravi)
- **Email:** [@supreethravi](mailto:connect@supreethravi.com)

This SDK provides implementation and tooling for the Agent Skills ecosystem.

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/agentskills/issues)
- **Documentation:** This README
- **Examples:** See `examples/` directory
