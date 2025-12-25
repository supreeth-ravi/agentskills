"""Tests for AgentSkillsClient."""

import pytest
from pathlib import Path

from agent_skills_sdk import AgentSkillsClient
from agent_skills_sdk.exceptions import SkillNotFoundError


class TestAgentSkillsClient:
    """Test cases for AgentSkillsClient."""

    @pytest.fixture
    def test_skills_path(self):
        """Get path to test skills directory."""
        return Path(__file__).parent.parent / "skills"

    @pytest.fixture
    def client(self, test_skills_path):
        """Create a test client."""
        return AgentSkillsClient(
            skill_paths=[str(test_skills_path)],
            auto_discover=True
        )

    def test_client_initialization(self, client):
        """Test that client initializes correctly."""
        assert client is not None
        assert len(client.skill_paths) > 0

    def test_discover_skills(self, client):
        """Test skill discovery."""
        skills = client.discover_skills()
        assert isinstance(skills, list)
        # Should find at least the example skill
        skill_names = [s.name for s in skills]
        assert "data-analysis" in skill_names

    def test_list_skills_metadata(self, client):
        """Test listing skill metadata."""
        metadata_list = client.list_skills()
        assert isinstance(metadata_list, list)
        assert len(metadata_list) > 0

    def test_load_skill(self, client):
        """Test loading a specific skill."""
        skill = client.load_skill("data-analysis")
        assert skill.name == "data-analysis"
        assert skill.description is not None
        assert len(skill.instructions) > 0

    def test_load_nonexistent_skill(self, client):
        """Test loading a skill that doesn't exist."""
        with pytest.raises(SkillNotFoundError):
            client.load_skill("nonexistent-skill")

    def test_get_metadata(self, client):
        """Test getting skill metadata."""
        metadata = client.get_metadata("data-analysis")
        assert metadata.name == "data-analysis"
        assert metadata.description is not None

    def test_get_instructions(self, client):
        """Test getting skill instructions."""
        instructions = client.get_instructions("data-analysis")
        assert isinstance(instructions, str)
        assert len(instructions) > 0

    def test_search_skills(self, client):
        """Test searching for skills."""
        # Search by tag
        results = client.search_skills(tags=["data"])
        assert len(results) > 0

        # Search by query
        results = client.search_skills(query="analysis")
        assert len(results) > 0

    def test_validate_skill(self, client):
        """Test skill validation."""
        is_valid, errors = client.validate_skill("data-analysis")
        # May have errors if dependencies aren't installed, but should not crash
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    def test_skill_caching(self, client):
        """Test that skills are cached."""
        # Load skill twice
        skill1 = client.load_skill("data-analysis")
        skill2 = client.load_skill("data-analysis")

        # Should return same instance from cache
        assert skill1 is skill2


class TestSkillExecution:
    """Test skill tool execution."""

    @pytest.fixture
    def client(self):
        """Create client with test skills."""
        test_skills_path = Path(__file__).parent.parent / "skills"
        return AgentSkillsClient(
            skill_paths=[str(test_skills_path)],
            auto_discover=True
        )

    def test_tool_listing(self, client):
        """Test listing tools in a skill."""
        skill = client.load_skill("data-analysis")
        assert len(skill.tools) > 0
        tool_names = [t.name for t in skill.tools]
        assert "load-dataset" in tool_names

    @pytest.mark.skipif(
        not Path(__file__).parent.parent / "skills" / "data-analysis" / "scripts" / "load_dataset.py",
        reason="Test script not found"
    )
    def test_tool_execution_mock(self, client):
        """Test tool execution with mock data."""
        # This test requires pandas to be installed
        pytest.importorskip("pandas")

        # Create a simple test CSV
        import tempfile
        import csv

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'value'])
            writer.writerow(['test', '123'])
            test_file = f.name

        try:
            result = client.execute_tool(
                skill_name="data-analysis",
                tool_name="load-dataset",
                input_data={
                    "file_path": test_file,
                    "format": "csv"
                }
            )

            assert result.success
            assert result.data is not None
        finally:
            Path(test_file).unlink(missing_ok=True)
