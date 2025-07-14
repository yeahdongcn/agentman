#!/usr/bin/env python3
"""Test script to verify EXPOSE and CMD instructions are properly handled in Dockerfile generation."""

import os
import tempfile
from pathlib import Path

from agentman.agent_builder import AgentBuilder
from agentman.agentfile_parser import AgentfileParser


def test_dockerfile_generation_with_expose_and_cmd():
    """Test that EXPOSE and CMD instructions from Agentfile are included in generated Dockerfile."""

    # Create a test Agentfile content with EXPOSE and CMD instructions
    agentfile_content = """
FROM python:3.11-slim
MODEL anthropic/claude-3-sonnet-20241022
RUN apt-get update && apt-get install -y wget
EXPOSE 8080
EXPOSE 9090
CMD ["python", "agent.py"]
"""

    # Parse the Agentfile
    parser = AgentfileParser()
    config = parser.parse_content(agentfile_content)

    print("Parsed configuration:")
    print(f"Base image: {config.base_image}")
    print(f"Default model: {config.default_model}")
    print(f"Expose ports: {config.expose_ports}")
    print(f"CMD: {config.cmd}")
    print(f"Dockerfile instructions: {len(config.dockerfile_instructions)}")

    for i, instruction in enumerate(config.dockerfile_instructions):
        print(f"  {i}: {instruction.instruction} {instruction.args}")

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        # Build the agent
        builder = AgentBuilder(config, temp_dir)
        builder._generate_dockerfile()

        # Read the generated Dockerfile
        dockerfile_path = Path(temp_dir) / "Dockerfile"
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()

        print("\nGenerated Dockerfile:")
        print(dockerfile_content)

        # Verify EXPOSE and CMD instructions are present
        assert "EXPOSE 8080" in dockerfile_content, "EXPOSE 8080 not found in Dockerfile"
        assert "EXPOSE 9090" in dockerfile_content, "EXPOSE 9090 not found in Dockerfile"
        assert 'CMD ["python", "agent.py"]' in dockerfile_content, "CMD instruction not found in Dockerfile"
        assert "RUN apt-get update && apt-get install -y wget" in dockerfile_content, "Custom RUN instruction not found"

        print("\n✅ All checks passed! EXPOSE and CMD instructions are properly included.")


if __name__ == "__main__":
    test_dockerfile_generation_with_expose_and_cmd()
