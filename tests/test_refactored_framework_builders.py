"""Tests for the refactored framework builders using structured configuration."""

import pytest
from src.agentman.agentfile_parser import AgentfileParser
from src.agentman.agent_builder import AgentBuilder
from src.agentman.frameworks.fast_agent_builder import FastAgentConfig, FastAgentCodeGenerator
from src.agentman.frameworks.agno_builder import AgnoFrameworkConfig, AgnoCodeGenerator, AgnoConfigBuilder
import tempfile
from pathlib import Path


class TestRefactoredFrameworkBuilders:
    """Test the new structured framework builders."""

    def test_fast_agent_structured_config_creation(self):
        """Test that FastAgent uses structured configuration objects."""
        content = """
FROM yeahdongcn/agentman-base:latest
FRAMEWORK fast-agent
MODEL anthropic/claude-3-sonnet-20241022
AGENT helper
INSTRUCTION You are a helpful assistant
SERVERS web_search
"""
        parser = AgentfileParser()
        config = parser.parse_content(content)

        with tempfile.TemporaryDirectory() as temp_dir:
            builder = AgentBuilder(config, temp_dir)
            code = builder.framework.build_agent_content()

            # Verify structured approach produces expected output
            assert "FastAgent(" in code
            assert "@fast.agent(" in code
            assert 'name="helper"' in code
            assert 'instruction="""You are a helpful assistant"""' in code
            assert 'servers=["web_search"]' in code
            assert "asyncio.run(main())" in code

            # Verify no string concatenation artifacts
            assert not code.startswith('["')
            assert not "\\n" in code.replace("\\n", "")

    def test_agno_structured_config_creation(self):
        """Test that Agno uses structured configuration objects."""
        content = """
FROM yeahdongcn/agentman-base:latest
FRAMEWORK agno
MODEL anthropic/claude-3-sonnet-20241022
AGENT researcher
INSTRUCTION Research specialist
SERVERS web_search finance
"""
        parser = AgentfileParser()
        config = parser.parse_content(content)

        with tempfile.TemporaryDirectory() as temp_dir:
            builder = AgentBuilder(config, temp_dir)
            code = builder.framework.build_agent_content()

            # Verify structured approach produces expected output
            assert "from agno.agent import Agent" in code
            assert "from agno.models.anthropic import Claude" in code
            assert "from agno.tools.duckduckgo import DuckDuckGoTools" in code
            assert "from agno.tools.yfinance import YFinanceTools" in code
            assert "researcher_agent = Agent(" in code
            assert "Claude(id=" in code
            assert "DuckDuckGoTools()" in code
            assert "YFinanceTools(stock_price=True, analyst_recommendations=True)" in code

    def test_fast_agent_structured_builder_directly(self):
        """Test FastAgent structured builder directly."""
        config = FastAgentConfig(
            name="Test App",
            agents=[
                {
                    "name": "test_agent",
                    "instruction": "Test instruction",
                    "servers": ["web_search"],
                    "model": "gpt-4",
                    "use_history": True,
                    "human_input": False,
                    "default": False,
                }
            ],
            has_prompt_file=False,
        )

        generator = FastAgentCodeGenerator(config)
        code = generator.generate_complete_code()

        assert 'FastAgent("Test App")' in code
        assert '@fast.agent(' in code
        assert 'name="test_agent"' in code
        assert 'instruction="""Test instruction"""' in code
        assert 'servers=["web_search"]' in code
        assert 'model="gpt-4"' in code

    def test_agno_config_builder_directly(self):
        """Test Agno config builder directly."""
        builder = AgnoConfigBuilder()

        # Test model config building
        claude_config = builder.build_model_config("anthropic/claude-3-sonnet")
        assert claude_config.model_type == "claude"
        assert claude_config.model_id == "anthropic/claude-3-sonnet"

        openai_config = builder.build_model_config("openai/gpt-4")
        assert openai_config.model_type == "openai"
        assert openai_config.model_id == "openai/gpt-4"

        custom_config = builder.build_model_config("groq/mixtral-8x7b")
        assert custom_config.model_type == "custom"
        assert custom_config.model_id == "groq/mixtral-8x7b"
        assert custom_config.provider == "groq"

        # Test tool building
        tools = builder.build_tools_for_servers(["web_search", "finance"])
        assert len(tools) == 2
        tool_classes = [tool.tool_class for tool in tools]
        assert "DuckDuckGoTools" in tool_classes
        assert "YFinanceTools" in tool_classes

    def test_code_quality_improvements(self):
        """Test that refactored code has better structure and quality."""
        content = """
FROM yeahdongcn/agentman-base:latest
FRAMEWORK agno
MODEL anthropic/claude-3-sonnet-20241022
AGENT researcher
INSTRUCTION Research specialist  
SERVERS web_search
AGENT analyst  
INSTRUCTION Data analyst
SERVERS finance
"""
        parser = AgentfileParser()
        config = parser.parse_content(content)

        with tempfile.TemporaryDirectory() as temp_dir:
            builder = AgentBuilder(config, temp_dir)
            code = builder.framework.build_agent_content()

            # Verify clean structure
            lines = code.split('\n')

            # Check for proper imports organization
            import_section_found = False
            agent_section_found = False
            team_section_found = False
            main_section_found = False

            for line in lines:
                if line.startswith('import ') or line.startswith('from '):
                    import_section_found = True
                elif '= Agent(' in line:
                    agent_section_found = True
                elif '= Team(' in line:
                    team_section_found = True
                elif 'def main(' in line:
                    main_section_found = True

            assert import_section_found
            assert agent_section_found
            assert team_section_found  # Multiple agents should create team
            assert main_section_found

            # Verify no manual string concatenation artifacts
            assert "lines.extend([" not in code
            assert "\", \"" not in code  # No manual quote handling

            # Verify proper Python syntax
            try:
                compile(code, '<string>', 'exec')
            except SyntaxError:
                pytest.fail("Generated code has syntax errors")

    def test_backward_compatibility(self):
        """Test that refactored builders maintain backward compatibility."""
        # Test complex configuration that worked before
        content = """
FROM yeahdongcn/agentman-base:latest
FRAMEWORK fast-agent
MODEL anthropic/claude-3-sonnet-20241022

AGENT router_agent
INSTRUCTION Route requests to appropriate agents
MODEL openai/gpt-4
SERVERS web_search
DEFAULT true

ROUTER main_router
AGENTS router_agent
INSTRUCTION Route user requests
"""
        parser = AgentfileParser()
        config = parser.parse_content(content)

        with tempfile.TemporaryDirectory() as temp_dir:
            builder = AgentBuilder(config, temp_dir)
            code = builder.framework.build_agent_content()

            # Should generate both agent and router
            assert "@fast.agent(" in code
            assert "@fast.router(" in code
            assert "default=True" in code
            assert 'model="openai/gpt-4"' in code
            assert 'agents=["router_agent"]' in code
