"""Executor module - Executes individual plan steps using available tools.

The executor is responsible for:
1. Loading the appropriate tool based on the step specification
2. Invoking the tool with the provided parameters
3. Handling retries and fallbacks on failure
4. Returning structured results for the verifier
"""

from __future__ import annotations

import time
import logging
from typing import Any, Dict, List, Optional

from app.schemas import ToolResult

log = logging.getLogger(__name__)


class ToolRegistry:
    """Registry of available tools indexed by name."""
    
    def __init__(self, tools: Dict[str, Dict[str, Any]]) -> None:
        """Initialize the tool registry.
        
        Args:
            tools: Dict mapping tool names to tool specifications
                {tool_name: {"description": str, "parameters": dict, 
                             "function": callable, "fallback": callable}}
        """
        self.tools = tools
        self._validate_tools()
    
    def _validate_tools(self) -> None:
        """Validate that all registered tools have required fields."""
        for name, spec in self.tools.items():
            if "function" not in spec:
                log.warning(f"Tool '{name}' missing 'function' field")
    
    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get a tool specification by name.
        
        Args:
            tool_name: The name of the tool to retrieve
            
        Returns:
            Tool specification dict or None if not found
        """
        tool = self.tools.get(tool_name)
        if tool is None:
            log.warning(f"Tool '{tool_name}' not found in registry")
        return tool
    
    def list_tools(self) -> List[str]:
        """List all available tool names."""
        return list(self.tools.keys())


class Executor:
    """Executes plan steps using available tools.
    
    Handles:
    - Tool invocation with parameter validation
    - Retry logic with exponential backoff
    - Fallback execution on persistent failures
    - Timing and result tracking
    """
    
    def __init__(self, tool_registry: ToolRegistry, max_retries: int = 3) -> None:
        """Initialize the executor.
        
        Args:
            tool_registry: Registry of available tools
            max_retries: Maximum number of retry attempts per step
        """
        self.tool_registry = tool_registry
        self.max_retries = max_retries
    
    def execute_step(
        self, 
        step: "PlanStep", 
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Execute a single plan step.
        
        Args:
            step: The plan step to execute
            context: Optional execution context (previous results, etc.)
            
        Returns:
            ToolResult with execution outcome
        """
        tool_name = step.tool
        parameters = step.parameters.copy()
        
        # Inject context parameters if provided
        if context:
            parameters.update(context)
        
        tool_spec = self.tool_registry.get_tool(tool_name)
        if tool_spec is None:
            return ToolResult(
                step_id=step.step_id,
                success=False,
                error=f"Tool '{tool_name}' not found in registry",
                execution_time_s=0.0,
            )
        
        func = tool_spec["function"]
        tool_desc = tool_spec.get("description", "")
        
        log.info(f"Executing step {step.step_id}: {tool_name}")
        start_time = time.perf_counter()
        
        # Attempt execution with retries
        last_exception: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                result = func(**parameters)
                # Ensure result is a dict-like object
                if not isinstance(result, dict):
                    result = {"output": result}
                
                execution_time = time.perf_counter() - start_time
                return ToolResult(
                    step_id=step.step_id,
                    success=True,
                    data=result,
                    execution_time_s=round(execution_time, 3),
                )
                
            except Exception as err:  # noqa: BLE001
                last_exception = err
                wait_time = 2 ** attempt * 1.5  # Exponential backoff
                log.warning(
                    f"Step {step.step_id} attempt {attempt + 1} failed: {err}; "
                    f"retrying in {wait_time:.1f}s"
                )
                if attempt < self.max_retries:
                    time.sleep(wait_time)
        
        # All retries exhausted
        execution_time = time.perf_counter() - start_time
        return ToolResult(
            step_id=step.step_id,
            success=False,
            error=f"Failed after {self.max_retries + 1} attempts: {last_exception}",
            execution_time_s=round(execution_time, 3),
        )
    
    def execute_plan(
        self, 
        plan: "ExecutionPlan", 
        context: Optional[Dict[str, Any]] = None
    ) -> List[ToolResult]:
        """Execute all steps in a plan sequentially.
        
        Args:
            plan: The execution plan
            context: Optional initial execution context
            
        Returns:
            List of ToolResult one per step
        """
        log.info(f"Executing plan with {len(plan.steps)} steps")
        results: List[ToolResult] = []
        execution_context: Dict[str, Any] = context or {}
        
        for step in plan.steps:
            # Execute step and capture result
            result = self.execute_step(step, execution_context)
            results.append(result)
            
            # Update context with successful step data for downstream steps
            if result.success and result.data:
                # Store result under step_id for downstream reference
                execution_context[f"step_{step.step_id}_result"] = result.data
                # Also expose key fields based on tool type
                if "search_results" in result.data:
                    execution_context["search_results"] = result.data["search_results"]
                if "job_analysis" in result.data:
                    execution_context["job_analysis"] = result.data["job_analysis"]
                if "skill_gap_analysis" in result.data:
                    execution_context["skill_gap_analysis"] = result.data["skill_gap_analysis"]
        
        log.info(f"Plan execution complete: {sum(1 for r in results if r.success)}/{len(results)} successful")
        return results