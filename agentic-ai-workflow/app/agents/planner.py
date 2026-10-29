"""Planner module - Breaks down user requests into executable steps.

The planner analyzes a natural language user request and decomposes it into
a structured execution plan with individual steps, tool selections, and
parameters. It uses the LLM to understand intent and map it to available
tools and their parameters.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from support_ai.schemas import UserRequest, PlanStep, ExecutionPlan, AgentResponse

log = logging.getLogger(__name__)


class Planner:
    """Decomposes user requests into executable plan steps."""
    
    def __init__(self, llm_client, available_tools: Dict[str, Dict[str, Any]]) -> None:
        """Initialize the planner.
        
        Args:
            llm_client: An LLM client compatible with the OpenAI format
            available_tools: Dict mapping tool names to their specifications
                {tool_name: {"description": str, "parameters": dict, "function": callable}}
        """
        self.llm_client = llm_client
        self.available_tools = available_tools
    
    def plan(self, request: UserRequest) -> ExecutionPlan:
        """Generate an execution plan from a user request.
        
        Args:
            request: The parsed user request
            
        Returns:
            ExecutionPlan with all steps needed to fulfill the request
        """
        log.info(f"Planning request: {request.text[:100]}...")
        
        # Build the tool catalog for the LLM
        tool_catalog = self._build_tool_catalog()
        
        # Generate the plan using the LLM
        plan_text = self._generate_plan_with_llm(request.text, tool_catalog)
        
        # Parse the plan from LLM response
        plan = self._parse_plan(plan_text, request.request_id)
        
        log.info(f"Generated plan with {len(plan.steps)} steps")
        return plan
    
    def _build_tool_catalog(self) -> str:
        """Build a text catalog of available tools for the LLM."""
        lines = ["Available tools:"]
        for name, spec in self.available_tools.items():
            lines.append(
                f"- {name}: {spec['description']}"
                f"Parameters: {spec.get('parameters', '{}')}"
            )
        return "\n".join(lines)
    
    def _generate_plan_with_llm(self, user_text: str, tool_catalog: str) -> str:
        """Generate a plan using the LLM."""
        prompt = f"""You are an autonomous AI workflow planner. Your task is to decompose a user's 
natural language request into a structured sequence of steps that can be executed by tools.

User request: "{user_text}"

{tool_catalog}

Generate a plan in JSON format with this exact structure:
{{
  "steps": [
    {{
      "step_id": "unique-step-1",
      "name": "Step name",
      "description": "What this step does",
      "tool": "tool_name",
      "parameters": {{}},
      "depends_on": []
    }}
  ]
}}

Rules:
1. each step must have a unique step_id, a descriptive name, a clear description,
   the tool name to use, and parameters specific to that tool
2. Use the available tools above - do not invent new tool names
3. If the request requires multiple steps, create them in logical order
4. Set depends_on appropriately for sequential or parallel execution
5. The final step should verify/confirm completion
6. Return ONLY the JSON, no surrounding text or explanations"""

        messages = [
            {"role": "system", "content": "You are a precise workflow planner. Output valid JSON only."},
            {"role": "user", "content": prompt},
        ]
        
        response = self.llm_client.complete(messages, temperature=0.0)
        
        # Try to extract JSON from the response
        try:
            # Attempt to find JSON block
            start = response.content.find("{")
            end = response.content.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response.content[start:end]
                plan_data = json.loads(json_str)
                return plan_data
        except (json.JSONDecodeError, ValueError) as e:
            log.warning(f"Failed to parse plan JSON: {e}")
        
        # Fallback: return a basic plan
        return {"steps": []}
    
    def _parse_plan(self, plan_data: Dict[str, Any], request_id: str) -> ExecutionPlan:
        """Parse and validate the plan data into an ExecutionPlan."""
        steps = []
        
        for step_data in plan_data.get("steps", []):
            # Merge request context into parameters
            parameters = step_data.get("parameters", {})
            parameters["request_id"] = request_id
            parameters["user_text"] = plan_data.get("original_text", "")
            
            step = PlanStep(
                step_id=step_data.get("step_id", f"step-{len(steps)+1}"),
                name=step_data.get("name", "Unnamed step"),
                description=step_data.get("description", ""),
                tool=step_data.get("tool", ""),
                parameters=parameters,
                depends_on=step_data.get("depends_on", []),
            )
            steps.append(step)
        
        return ExecutionPlan(
            request_id=request_id,
            steps=steps,
            created_at=self._get_current_timestamp(),
            estimated_total_duration_s=self._estimate_total_duration(steps),
        )
    
    @staticmethod
    def _get_current_timestamp() -> str:
        """Get the current ISO format timestamp."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    @staticmethod
    def _estimate_total_duration(steps: List[PlanStep]) -> float:
        """Estimate total execution duration based on steps."""
        # Simple estimation: 2s per step + parameter-dependent
        return len(steps) * 2.0