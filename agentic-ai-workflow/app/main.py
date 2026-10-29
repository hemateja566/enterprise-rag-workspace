"""FastAPI main application for the Agentic AI Workflow Assistant.

Exposes endpoints for:
1. Submitting user requests and getting complete agent workflow execution
2. Checking agent health status
3. Managing memory (short-term and long-term)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from support_ai.config import SETTINGS

# Import our modules
from app.schemas import (
    UserRequest,
    ExecutionPlan,
    AgentResponse,
    VerificationResult,
    PlanStep,
)
from app.agents.planner import Planner
from app.agents.executor import Executor, ToolRegistry
from app.agents.verifier import Verifier
from app.memory import ShortTermMemory, LongTermMemory
from app.tools.search import SearchTool
from app.tools.job_search import JobSearchTool
from app.tools.skill_analysis import SkillAnalysisTool

# Try to initialize tools, gracefully degrade if API keys missing
try:
    search_tool = SearchTool(api_key=os.getenv("TAVILY_API_KEY", ""))
    job_search_tool = JobSearchTool(search_tool)
    skill_analysis_tool = SkillAnalysisTool()
    available_tools = {
        "search": {
            "description": "Web search using Tavily API",
            "parameters": {"query": {"type": "string"}, "max_results": {"type": "integer"}},
            "function": search_tool.search,
        },
        "job_search": {
            "description": "Search for job opportunities",
            "parameters": {
                "title": {"type": "string"},
                "location": {"type": "string"},
                "skills": {"type": "list", "items": {"type": "string"}},
                "experience_level": {"type": "string"},
            },
            "function": job_search_tool.search_jobs,
        },
        "skill_analysis": {
            "description": "Analyze skills gap between jobs and user",
            "parameters": {
                "job_descriptions": {"type": "list", "items": {"type": "string"}},
                "user_skills": {"type": "list", "items": {"type": "string"}},
            },
            "function": skill_analysis_tool.analyze_skills,
        },
    }
    tools_registry = ToolRegistry(available_tools)
except Exception as e:
    log.warning(f"Tool initialization failed: {e}")
    search_tool = None
    job_search_tool = None
    skill_analysis_tool = None
    available_tools = {}
    tools_registry = ToolRegistry({})


# ── LLM Client Mock (replace with real client in production) ──────────────────

class MockLLMClient:
    """A minimal LLM client mimicking the OpenAI chat completions API."""
    
    def complete(self, messages: list[dict], **kwargs) -> Any:
        """Return a simple text response based on the prompt."""
        # Extract the user message
        user_msg = next(
            (m.get("content", "") for m in messages if m.get("role") == "user"), ""
        )
        
        # Simple keyword-based responses for demo purposes
        content = user_msg.lower()
        
        if "job" in content and "ai" in content:
            response_text = json.dumps({
                "steps": [
                    {
                        "step_id": "step-1",
                        "name": "Search AI job opportunities",
                        "description": "Search for AI job openings",
                        "tool": "job_search",
                        "parameters": {"title": "AI Engineer", "location": "Remote"},
                    },
                    {
                        "step_id": "step-2",
                        "name": "Analyze required skills",
                        "description": "Extract required skills from job descriptions",
                        "tool": "skill_analysis",
                        "parameters": {"job_descriptions": []},
                    },
                    {
                        "step_id": "step-3",
                        "name": "Create preparation plan",
                        "description": "Generate a personalized preparation plan",
                        "tool": "skill_analysis",
                        "parameters": {"user_skills": ["python", "sql"]},
                    },
                ]
            })
        elif "skill" in content:
            response_text = json.dumps({
                "steps": [
                    {
                        "step_id": "step-1",
                        "name": "Analyze skills",
                        "description": "Analyze required skills",
                        "tool": "skill_analysis",
                        "parameters": {"user_skills": ["python", "javascript"]},
                    }
                ]
            })
        else:
            response_text = json.dumps({
                "steps": [
                    {
                        "step_id": "step-1",
                        "name": "Process request",
                        "description": "Process the user request",
                        "tool": "search",
                        "parameters": {"query": content[:50] if content else "latest AI jobs"},
                    }
                ]
            })
        
        class _Response:
            content = response_text
        
        return _Response()


llm_client = MockLLMClient()

# ── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Agentic AI Workflow Assistant",
    version="1.0.0",
    description="""
    Autonomous AI agent that can understand user requests, plan multi-step workflows,
    select and execute tools, and verify results.
    
    Example use case:
    - User: "Research the latest AI job opportunities, analyze the required skills, 
      and create a preparation plan."
    - Agent searches for jobs, extracts skills, identifies gaps, and generates a plan.
    """,
)


# ── Pydantic models for API endpoints ─────────────────────────────────────────

class PlanRequest(BaseModel):
    """Request to generate and execute an execution plan."""
    text: str = Field(..., description="The user's natural language request")
    request_id: Optional[str] = Field(None, description="Optional request ID for tracking")
    session_id: Optional[str] = Field(None, description="Optional session ID for memory")
    user_skills: Optional[List[str]] = Field(
        None, description="Optional user's current skills list"
    )


class PlanResponse(BaseModel):
    """Response containing the full agent workflow result."""
    request_id: str
    plan: ExecutionPlan
    results: List[Dict[str, Any]]
    verification: VerificationResult
    final_output: str
    execution_log: List[Dict[str, Any]]


# ── Lifecycle: Initialize memory ──────────────────────────────────────────────

short_term_memory: ShortTermMemory = ShortTermMemory(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=int(os.getenv("REDIS_DB", "0")),
)

long_term_memory: LongTermMemory = LongTermMemory(
    db_name=os.getenv("POSTGRES_DB", "agentic_ai"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "password"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
)


# ── API Endpoints ────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "Agentic AI Workflow Assistant"}


@app.post("/plan-and-execute", response_model=PlanResponse)
def plan_and_execute(request: PlanRequest) -> PlanResponse:
    """Process a user request through the full agent workflow.
    
    The workflow includes:
    1. Planning: Decompose the request into executable steps
    2. Execution: Run each step using appropriate tools
    3. Verification: Check that the request was satisfied
    4. Output: Generate a final summary
    
    Args:
        request: The user request and optional parameters
        
    Returns:
        Complete agent response with plan, results, and verification
    """
    # Generate or use request ID
    request_id = request.request_id or f"req-{int(time.time())}"
    
    # Store user skills in short-term memory if provided
    if request.user_skills:
        short_term_memory.set(
            f"user_skills:{request_id}",
            {"skills": request.user_skills},
            ttl=3600,
        )
    
    # Step 1: Plan the request
    try:
        user_request = UserRequest(
            text=request.text,
            request_id=request_id,
            context={"session_id": request.session_id, "user_skills": request.user_skills},
        )
        
        planner = Planner(llm_client, available_tools)
        execution_plan: ExecutionPlan = planner.plan(user_request)
        
        # Store the plan in short-term memory
        short_term_memory.set(
            f"plan:{request_id}",
            execution_plan.model_dump(),
            ttl=3600,
        )
        
    except Exception as e:
        log.error(f"Planning failed: {e}")
        raise HTTPException(status_code=500, detail=f"Planning failed: {str(e)}")
    
    # Step 2: Execute the plan
    try:
        executor = Executor(tools_registry, max_retries=3)
        results: List[Any] = executor.execute_plan(execution_plan)
        
        # Convert results to dicts for serialization
        results_dicts = [r.model_dump() if hasattr(r, 'model_dump') else dict(r) for r in results]
        
        # Store results in short-term memory
        short_term_memory.set(
            f"results:{request_id}",
            results_dicts,
            ttl=3600,
        )
        
    except Exception as e:
        log.error(f"Plan execution failed: {e}")
        # Return error results
        results_dicts = []
    
    # Step 3: Verify completion
    try:
        verification = Verifier(llm_client).verify(user_request, results_dicts, execution_plan)
        
        # Store verification in short-term memory
        short_term_memory.set(
            f"verification:{request_id}",
            verification.model_dump() if hasattr(verification, 'model_dump') else dict(verification),
            ttl=3600,
        )
        
    except Exception as e:
        log.error(f"Verification failed: {e}")
        verification = VerificationResult(
            request_id=request_id,
            success=False,
            summary="Verification error occurred",
            confidence=0.0,
            recommended_actions=["Review the request and try again"],
        )
    
    # Step 4: Generate final output
    final_output = _generate_final_output(execution_plan, results_dicts, verification)
    
    # Step 5: Store in long-term memory for persistence
    try:
        long_term_memory.store_workflow(
            workflow_id=request_id,
            user_request=request.text,
            plan=execution_plan.model_dump() if hasattr(execution_plan, 'model_dump') else dict(execution_plan),
            results={f"step_{r.step_id}": r.data if hasattr(r, 'data') and r.data else {} for r in results_dicts},
            verification=verification.model_dump() if hasattr(verification, 'model_dump') else dict(verification),
            final_output=final_output,
            status="completed" if verification.success else "partial",
        )
    except Exception as e:
        log.warning(f"Failed to store in long-term memory: {e}")
    
    # Build execution log
    execution_log = _build_execution_log(execution_plan, results_dicts, verification)
    
    return PlanResponse(
        request_id=request_id,
        plan=execution_plan,
        results=results_dicts,
        verification=verification,
        final_output=final_output,
        execution_log=execution_log,
    )


def _generate_final_output(
    plan: ExecutionPlan,
    results: List[Dict[str, Any]],
    verification: VerificationResult,
) -> str:
    """Generate a human-readable final output summary."""
    parts = []
    
    # Plan summary
    parts.append(f"## Execution Plan")
    parts.append(f"Steps: {len(plan.steps)}")
    for step in plan.steps:
        parts.append(f"- {step.name} ({step.tool})")
    
    # Results summary
    parts.append(f"\n## Results")
    successful = [r for r in results if r.get("success", False)]
    parts.append(f"Steps completed successfully: {len(successful)}/{len(results)}")
    
    if verification.success:
        parts.append(f"\n## ✅ Verification")
        parts.append(f"Summary: {verification.summary}")
        if verification.recommended_actions:
            parts.append(f"Recommended actions: {', join(verification.recommended_actions)}")
    else:
        parts.append(f"\n## ⚠️ Verification")
        parts.append(f"Summary: {verification.summary}")
        if verification.recommended_actions:
            parts.append(f"Recommended actions: {', '.join(verification.recommended_actions)}")
    
    return "\n".join(parts)


def _build_execution_log(
    plan: ExecutionPlan,
    results: List[Dict[str, Any]],
    verification: VerificationResult,
) -> List[Dict[str, Any]]:
    """Build a detailed execution log."""
    log_entries = []
    
    # Plan start
    log_entries.append({
        "timestamp": "__init__",
        "event": "plan_created",
        "step_count": len(plan.steps),
        "request_id": plan.request_id,
    })
    
    # Each step
    for i, step in enumerate(plan.steps):
        result_data = {}
        if i < len(results):
            result_data = results[i] if isinstance(results[i], dict) else {}
        
        log_entries.append({
            "step_index": i,
            "step_id": step.step_id,
            "step_name": step.name,
            "tool": step.tool,
            "success": result_data.get("success", False),
            "execution_time": result_data.get("execution_time_s", 0),
        })
    
    # Verification
    log_entries.append({
        "event": "verification",
        "success": verification.success,
        "confidence": verification.confidence,
    })
    
    return log_entries


# Run the app with: uvicorn api.main:app --port 8000
# (When run directly)
if __name__ == "__main__":
    import uvicorn
    import time
    
    print("Starting Agentic AI Workflow Assistant...")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)