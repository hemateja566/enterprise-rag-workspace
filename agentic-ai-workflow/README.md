# Agentic AI Workflow Assistant

An autonomous AI agent that can understand user requests, plan multi-step workflows,
select and execute tools, and verify results.

## Overview

This project demonstrates agent orchestration, state management, tool calling, and
autonomous workflow development. The agent can:

1. **Understand** natural language user requests
2. **Plan** multi-step workflows with tool selection
3. **Execute** tasks using integrated tools (search, job analysis, skill gap analysis)
4. **Verify** results and generate summaries

## Tech Stack

- **Language**: Python 3.12
- **Agent Framework**: LangGraph (integrated)
- **LLM**: Hugging Face Inference Router (compatible with OpenAI API)
- **Web API**: FastAPI
- **Search**: Tavily API
- **Database**: PostgreSQL (long-term memory)
- **Cache**: Redis (short-term memory)
- **Containerization**: Docker

## Project Structure

```
agentic-ai-workflow/
├── app/                    # Main application package
│   ├── __init__.py
│   ├── main.py            # FastAPI entry point
│   ├── schemas.py         # Pydantic models
│   └── agents/            # Agent modules
│       ├── __init__.py
│       ├── planner.py     # Request decomposition
│       ├── executor.py    # Tool execution
│       ├── verifier.py    # Result verification
│       └── memory.py      # Memory management
├── tools/                  # Tool implementations
│   ├── __init__.py
│   ├── search.py          # Web search (Tavily)
│   ├── job_search.py    # Job opportunity search
│   └── skill_analysis.py # Skill gap analysis
├── memory/                 # Memory systems
│   ├── __init__.py
│   ├── short_term.py      # Redis-backed
│   └── long_term.py       # PostgreSQL-backed
├── prompts/                # Prompt templates
├── scripts/                # Setup scripts
├── Dockerfile             # Container configuration
├── README.md              # This file
└── requirements.txt       # Python dependencies
```

## Features

### Core Capabilities
- **Request Planning**: Decomposes natural language requests into structured execution plans
- **Tool Execution**: Invokes appropriate tools with retry and fallback mechanisms
- **Result Verification**: Checks that user requests are fully satisfied
- **Memory Management**: Short-term (Redis) and long-term (PostgreSQL) memory

### Advanced Features
- **Multi-tool Integration**: Combines search, job analysis, and skill gap tools
- **Retry Logic**: Exponential backoff with configurable max retries
- **Fallback Handling**: Graceful degradation when tools are unavailable
- **Execution Logging**: Full traceability of all steps and results
- **Persistent Storage**: Workflow history and user profiles

### API Endpoints

- `GET /health` - Health check
- `POST /plan-and-execute` - Process a full agent workflow

## Usage

### Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables in `.env`:
   ```
   TAVILY_API_KEY=your_tavily_key
   HF_TOKEN=your_hf_token
   REDIS_HOST=localhost
   POSTGRES_DB=agentic_ai
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   ```

3. Start the services:
   ```bash
   # Start Redis
   redis-server --daemonize yes
   
   # Start PostgreSQL (docker recommended)
   docker run -d -p 5432:5432 --name pg-db -e POSTGRES_PASSWORD=password postgres:15
   
   # Run the application
   uvicorn app.main:app --port 8000
   ```

4. Test the agent:
   ```bash
   curl -X POST "http://localhost:8000/plan-and-execute" \
     -H "Content-Type: application/json" \
     -d '{"text": "Research the latest AI job opportunities, analyze the required skills, and create a preparation plan."}'
   ```

### API Example

```bash
# Research AI jobs, analyze skills, create prep plan
curl -X POST "http://localhost:8000/plan-and-execute" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Research the latest AI job opportunities, analyze the required skills, and create a preparation plan.",
    "user_skills": ["python", "sql"]
  }'
```

Response includes:
- `plan`: The execution plan with all steps
- `results`: Tool output from each step
- `verification`: Whether the request was satisfied
- `final_output`: Human-readable summary
- `execution_log`: Complete trace of execution

## Docker Deployment

```bash
# Build the image
docker build -t agentic-ai-workflow .

# Run with environment
docker run -d \
  -p 8000:8000 \
  -e TAVILY_API_KEY=your_key \
  -e HF_TOKEN=your_hf_token \
  -e POSTGRES_DB=agentic_ai \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e REDIS_HOST=localhost \
  agentic-ai-workflow
```

## Development

### Adding New Tools
1. Create a new tool in `tools/` following the existing pattern
2. Add the tool to `available_tools` in `app/main.py`
3. Update the planner's tool catalog if needed

### Extending the Agent
- Add more prompt templates in `prompts/`
- Extend memory capabilities in `memory/`
- Add new verification logic in `verifier/`
- Integrate with additional APIs in the tools

## License

This project is for demonstration and evaluation purposes.