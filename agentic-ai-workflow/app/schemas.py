"""Pydantic schemas for the Agentic AI Workflow Assistant."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UserRequest(BaseModel):
    """A user's natural language request to the agent."""

    text: str = Field(..., description="The raw user request text")
    request_id: Optional[str] = Field(None, description="Optional unique identifier for tracking")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Optional contextual information (user profile, etc.)"
    )


class PlanStep(BaseModel):
    """A single step in the agent's execution plan."""

    step_id: str = Field(..., description="Unique step identifier")
    name: str = Field(..., description="Human-readable step name")
    description: str = Field(..., description="What this step does")
    tool: str = Field(..., description="Tool to execute")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Parameters for the tool"
    )
    depends_on: Optional[List[str]] = Field(
        None, description "Step IDs this step depends on"
    )
    estimated_duration_s: Optional[float] = Field(
        None, description="Estimated duration in seconds"
    )


class ExecutionPlan(BaseModel):
    """A complete execution plan generated from a user request."""

    request_id: str
    steps: List[PlanStep]
    created_at: str
    estimated_total_duration_s: float


class ToolResult(BaseModel):
    """Result returned from tool execution."""

    step_id: str
    success: bool
    data: Optional[Dict[str, Any]] = Field(None, description="Tool output data")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time_s: float


class VerificationResult(BaseModel):
    """Result of verifying task completion."""

    request_id: str
    success: bool
    summary: str
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score (0-1)"
    )
    recommended_actions: List[str] = Field(
        default_factory=list, description="Suggested next steps"
    )


class AgentResponse(BaseModel):
    """Complete response from the agent."""

    request_id: str
    plan: ExecutionPlan
    results: List[ToolResult]
    verification: VerificationResult
    final_output: str
    execution_log: List[Dict[str, Any]]