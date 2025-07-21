#!/usr/bin/env python3
"""Test script to verify prompt.txt support in AgentBuilder."""

import os
import tempfile
from pathlib import Path

from agentman.agent_builder import AgentBuilder
from agentman.agentfile_parser import AgentfileParser


def test_prompt_txt_support():
    """Test that prompt.txt is copied and integrated when it exists."""

    # Create a test Agentfile content
    agentfile_content = """
FROM ghcr.io/o3-cloud/agentman/base:main
MODEL anthropic/claude-3-sonnet-20241022

AGENT test_agent
INSTRUCTION You are a helpful test agent.
"""

    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_source_dir:
        with tempfile.TemporaryDirectory() as temp_output_dir:
            # Create source directory structure
            source_path = Path(temp_source_dir)
            agentfile_path = source_path / "Agentfile"
            prompt_path = source_path / "prompt.txt"

            # Write Agentfile
            with open(agentfile_path, 'w') as f:
                f.write(agentfile_content)

            # Write prompt.txt
            prompt_content = "Test prompt content for the agent"
            with open(prompt_path, 'w') as f:
                f.write(prompt_content)

            # Parse the Agentfile
            parser = AgentfileParser()
            config = parser.parse_file(str(agentfile_path))

            # Build with prompt.txt
            builder = AgentBuilder(config, temp_output_dir, temp_source_dir)
            builder.build_all()

            # Verify prompt.txt was copied
            output_prompt_path = Path(temp_output_dir) / "prompt.txt"
            assert output_prompt_path.exists(), "prompt.txt should be copied to output directory"

            with open(output_prompt_path, 'r') as f:
                copied_content = f.read()
            assert copied_content == prompt_content, "prompt.txt content should match"

            # Verify agent.py contains prompt loading logic
            agent_py_path = Path(temp_output_dir) / "agent.py"
            with open(agent_py_path, 'r') as f:
                agent_content = f.read()

            assert "prompt_file = 'prompt.txt'" in agent_content, "Agent should check for prompt.txt"
            assert (
                "with open(prompt_file, 'r', encoding='utf-8') as f:" in agent_content
            ), "Agent should read prompt.txt"
            assert "await agent(prompt_content)" in agent_content, "Agent should use prompt content"

            # Verify Dockerfile contains COPY prompt.txt
            dockerfile_path = Path(temp_output_dir) / "Dockerfile"
            with open(dockerfile_path, 'r') as f:
                dockerfile_content = f.read()

            assert "COPY prompt.txt ." in dockerfile_content, "Dockerfile should copy prompt.txt"

            print("✅ prompt.txt support test passed!")


def test_no_prompt_txt_backward_compatibility():
    """Test that builds work normally when prompt.txt doesn't exist."""

    # Create a test Agentfile content
    agentfile_content = """
FROM ghcr.io/o3-cloud/agentman/base:main
MODEL anthropic/claude-3-sonnet-20241022

AGENT test_agent
INSTRUCTION You are a helpful test agent.
"""

    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_source_dir:
        with tempfile.TemporaryDirectory() as temp_output_dir:
            # Create source directory structure (no prompt.txt)
            source_path = Path(temp_source_dir)
            agentfile_path = source_path / "Agentfile"

            # Write Agentfile
            with open(agentfile_path, 'w') as f:
                f.write(agentfile_content)

            # Parse the Agentfile
            parser = AgentfileParser()
            config = parser.parse_file(str(agentfile_path))

            # Build without prompt.txt
            builder = AgentBuilder(config, temp_output_dir, temp_source_dir)
            builder.build_all()

            # Verify prompt.txt was NOT copied
            output_prompt_path = Path(temp_output_dir) / "prompt.txt"
            assert not output_prompt_path.exists(), "prompt.txt should not exist in output directory"

            # Verify agent.py contains standard logic
            agent_py_path = Path(temp_output_dir) / "agent.py"
            with open(agent_py_path, 'r') as f:
                agent_content = f.read()

            assert "prompt_file = 'prompt.txt'" not in agent_content, "Agent should not check for prompt.txt"
            assert "await agent()" in agent_content, "Agent should use standard call"

            # Verify Dockerfile does NOT contain COPY prompt.txt
            dockerfile_path = Path(temp_output_dir) / "Dockerfile"
            with open(dockerfile_path, 'r') as f:
                dockerfile_content = f.read()

            assert "COPY prompt.txt ." not in dockerfile_content, "Dockerfile should not copy prompt.txt"

            print("✅ backward compatibility test passed!")


if __name__ == "__main__":
    test_prompt_txt_support()
    test_no_prompt_txt_backward_compatibility()
    print("🎉 All tests passed!")
