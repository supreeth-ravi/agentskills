#!/bin/bash
# Setup script for Agent Skills SDK

set -e

echo "========================================="
echo "Agent Skills SDK - Setup"
echo "========================================="
echo ""

# Check Python version
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    echo "✓ Python version: $python_version"
else
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created at .venv/"
else
    echo "✓ Virtual environment exists at .venv/"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"

# Install package in development mode
echo "Installing Agent Skills SDK..."
pip install -e . > /dev/null 2>&1
echo "✓ SDK installed in development mode"

# Verify installation
echo ""
echo "Verifying installation..."
python -c "from agent_skills_sdk import AgentSkillsClient; print('✓ AgentSkillsClient imported successfully')"
python -c "from agent_skills_sdk.adapters import AgnoAdapter; print('✓ AgnoAdapter imported successfully')"

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Quick Start:"
echo "  1. Activate: source .venv/bin/activate"
echo "  2. Run validation: python examples/validate.py"
echo "  3. Try Python example: python examples/python/agent.py"
echo ""
echo "Framework Examples (require API keys):"
echo "  • Agno: python examples/agno/agent.py"
echo "  • LangChain: python examples/langchain/agent.py"
echo "  • CrewAI: python examples/crewai/agent.py"
echo ""
echo "Documentation:"
echo "  • README.md - Main documentation"
echo "  • docs/ - Additional guides"
echo ""
