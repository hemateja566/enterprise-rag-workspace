"""Verifier module - Checks results and determines task completion.

The verifier analyzes the execution results to:
1. Determine if the overall request has been satisfied
2. Assess confidence in the results
3. Identify any gaps or required follow-up actions
4. Generate a summary verification result
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from support_ai.schemas import VerificationResult, AgentResponse

log = logging.getLogger(__name__)


class Verifier:
    """Verifies that a user's request has been fully satisfied."""
    
    def __init__(self, llm_client=None) -> None:
        """Initialize the verifier.
        
        Args:
            llm_client: Optional LLM client for complex verification reasoning
        """
        self.llm_client = llm_client
    
    def verify(self, 
               request: "UserRequest", 
               results: List["ToolResult"], 
               plan: "ExecutionPlan") -> VerificationResult:
        """Verify that the request has been satisfied by the execution results.
        
        Args:
            request: The original user request
            results: List of ToolResult from executing the plan
            plan: The original execution plan
            
        Returns:
            VerificationResult indicating success, confidence, and recommendations
        """
        log.info("Verifying request completion")
        
        # Count successful vs failed steps
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        # Determine overall success
        all_successful = all(r.success for r in results)
        
        # If all steps succeeded, check if the results make sense for the request
        if all_successful:
            confidence = self._calculate_confidence(results, plan)
            summary = self._generate_summary(results, request)
            recommended_actions = self._identify_actions(results, plan)
        else:
            # Some steps failed
            confidence = self._calculate_confidence_on_failure(results, failed)
            summary = self._generate_failure_summary(results, request)
            recommended_actions = self._identify_failure_actions(failed, plan)
        
        return VerificationResult(
            request_id=request.request_id or "",
            success=all_successful,
            summary=summary,
            confidence=confidence,
            recommended_actions=recommended_actions,
        )
    
    def _calculate_confidence(self, results: List["ToolResult"], plan: "ExecutionPlan") -> float:
        """Calculate confidence score based on step results and plan quality."""
        if not results:
            return 0.0
        
        # Base confidence from success rate
        success_rate = sum(1 for r in results if r.success) / len(results)
        
        # Adjust based on execution times (faster is generally better)
        avg_time = sum(r.execution_time_s for r in results) / len(results)
        time_factor = min(1.0, 5.0 / max(avg_time, 0.1))
        
        # Combine factors
        confidence = round(0.7 * success_rate + 0.3 * time_factor, 2)
        return max(0.0, min(1.0, confidence))
    
    def _calculate_confidence_on_failure(self, results: List["ToolResult"], failed: List["ToolResult"]) -> float:
        """Calculate confidence when some steps failed."""
        if not results:
            return 0.0
        success_rate = sum(1 for r in results if r.success) / len(results)
        return round(success_rate, 2)
    
    def _generate_summary(self, results: List["ToolResult"], request: "UserRequest") -> str:
        """Generate a human-readable summary of successful results."""
        successful_data = []
        for r in results:
            if r.success and r.data:
                successful_data.append(r.data)
        
        if not successful_data:
            return "No successful results to summarize."
        
        # Create a brief summary based on what data we have
        summary_parts = []
        for data in successful_data:
            if "search_results" in data:
                n = len(data["search_results"])
                summary_parts.append(f"Found {n} search results")
            elif "job_analysis" in data:
                title = data["job_analysis"].get("title", "Unknown")
                summary_parts.append(f"Analyzed job: {title}")
            elif "skill_gap_analysis" in data:
                gaps = data["skill_gap_analysis"].get("gaps", [])
                summary_parts.append(f"Identified {len(gaps)} skill gaps")
            else:
                summary_parts.append(f"Result: {str(data)[:100]}")
        
        return " | ".join(summary_parts) if summary_parts else "Results obtained successfully."
    
    def _generate_failure_summary(self, results: List["ToolResult"], request: "UserRequest") -> str:
        """Generate summary when some steps failed."""
        failed_steps = [r for r in results if not r.success]
        success_steps = [r for r in results if r.success]
        
        parts = []
        if success_steps:
            parts.append(f"{len(success_steps)} step(s) succeeded")
        if failed_steps:
            error_summary = "; ".join(
                r.error[:80] if r.error else "unknown error" 
                for r in failed_steps
            )
            parts.append(f"{len(failed_steps)} step(s) failed: {error_summary}")
        
        return "; ".join(parts) if parts else "Verification completed with mixed results."
    
    def _identify_actions(self, results: List["ToolResult"], plan: "ExecutionPlan") -> List[str]:
        """Identify recommended actions based on results."""
        actions = []
        
        for r in results:
            if r.success and r.data:
                data = r.data
                if "search_results" in data and data["search_results"]:
                    actions.append("Review search results and select most relevant")
                if "job_analysis" in data:
                    actions.append("Review job analysis and match against personal skills")
                if "skill_gap_analysis" in data:
                    actions.append("Address identified skill gaps through training or experience")
        
        if not actions:
            actions.append("Review all execution results for completeness")
        
        return actions
    
    def _identify_failure_actions(self, failed: List["ToolResult"], plan: "ExecutionPlan") -> List[str]:
        """Identify actions when steps failed."""
        actions = []
        
        for r in failed:
            if r.error:
                actions.append(f"Retry step (original error: {r.error[:60]})")
        
        if not actions:
            actions.append("Review plan execution and adjust parameters")
        
        return actions
    
    def _identify_gaps(self, results: List["ToolResult"], plan: "ExecutionPlan") -> List[str]:
        """Identify any gaps in the execution coverage."""
        gaps = []
        tool_names = set(r.step_id for r in results)
        
        for step in plan.steps:
            if step.step_id not in tool_names:
                gaps.append(f"Step '{step.name}' was not executed")
        
        return gaps