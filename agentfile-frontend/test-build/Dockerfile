# Generated from Agentfile

FROM yeahdongcn/agentman-base:latest


# Secrets as build arguments
ARG DEEPSEEK_API_KEY
ARG DEEPSEEK_BASE_URL
ARG OPENAI_API_KEY
ARG OPENAI_BASE_URL

# Generate agent configuration
RUN mkdir -p /app/config
RUN echo '{
  "file": {
    "name": "file",
    "command": "uvx",
    "args": [
      "mcp-server-filesystem"
    ],
    "transport": "stdio"
  },
  "finance": {
    "name": "finance",
    "command": "uvx",
    "args": [
      "mcp-server-yfinance"
    ],
    "transport": "stdio"
  },
  "web_search": {
    "name": "web_search",
    "command": "uvx",
    "args": [
      "mcp-server-duckduckgo"
    ],
    "transport": "stdio"
  }
}' > /app/config/mcp_servers.json
RUN echo '{
  "content_creator": {
    "name": "content_creator",
    "instruction": "You are a content creator who synthesizes research findings into comprehensive reports, presentations, and summaries.",
    "servers": [
      "file"
    ],
    "model": "deepseek/deepseek-chat",
    "use_history": true,
    "human_input": false,
    "default": false
  },
  "data_analyst": {
    "name": "data_analyst",
    "instruction": "You are a financial data analyst specialized in stock analysis, market trends, and investment research. Provide detailed financial insights and recommendations.",
    "servers": [
      "finance",
      "file"
    ],
    "model": "openai/gpt-4o",
    "use_history": true,
    "human_input": false,
    "default": false
  },
  "research_coordinator": {
    "name": "research_coordinator",
    "instruction": "You are a research coordinator who plans and manages research projects. You analyze requirements, break down tasks, and coordinate with specialists.",
    "servers": [
      "web_search",
      "file"
    ],
    "model": "deepseek/deepseek-chat",
    "use_history": true,
    "human_input": false,
    "default": false
  }
}' > /app/config/agents.json

# Generate framework-specific code
RUN echo 'Generating AGNO agent code...' && \
    echo 'import agno' > /app/agent.py && \
    echo 'print("AGNO agent started")' >> /app/agent.py

WORKDIR /app

# Start command
CMD ["python","agent.py"]
