"""AI explanation/recommendation layer for financial goal evaluations.

Wraps the deterministic :mod:`goal_planner` results and prompts an LLM
(e.g. Groq) to:

1. Explain the calculations in plain language.
2. Personalise the recommendation based on the user's profile.
3. Present alternative strategies user-friendly.
4. Never recalculate numbers – only interpret the already-computed JSON.

A deterministic fallback template is provided so the endpoint always returns
a sensible message even if the LLM is unavailable or times out.

The module follows the patterns from the existing codebase:
- :class:`~support_ai.llm.LLMClient` / :class:`~support_ai.llm.ChatMessage`
- :class:`~support_ai.prompts.registry.Prompt` with versioning
- Structured output via :mod:`pydantic` (schema not required; dict returned)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from support_ai.config import SETTINGS
from support_ai.llm import LLMClient, LLMUnavailableError, get_client, ChatMessage
from support_ai.goal_planner import GoalStatus, SavingsPlan, evaluate_goal
from support_ai.prompts.registry import Prompt

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt templates (versioned for traceability)
# ---------------------------------------------------------------------------

GOAL_EXPLAIN = Prompt(
    name="goal.explain",
    version="1.0.0",
    template="""You are a friendly, knowledgeable financial mentor helping a user
understand their financial goal recommendation.

User context:
- Target goal: ₹{target:,.2f}
- Timeline: {months} months
- Monthly income: ₹{income:,.2f}
- Current savings: ₹{current_savings:,.2f}
- Monthly expenses: ₹{expenses:,.2f}
- Required monthly savings: ₹{required_monthly:,.2f}
- Savings ratio: {savings_ratio_percent:.1f}% of income
- Goal status: {status}

Feasibility message from the deterministic engine:
"{feasibility_message}"

User question: "{user_question}"

Instructions:
- Use ONLY the numbers above. Do NOT recalculate anything.
- Explain in 2-3 short paragraphs what the numbers mean, why the status is what it is,
  and what the user should do next.
- If the status is "stretch" or "not_feasible", present 2-3 alternative strategies
  from the `alternatives` list below, summarising each one in 1 sentence.
- Personalise the tone: acknowledge the user's situation, be encouraging but
  realistic.
- End with a clear, actionable next step.
- Return the response as plain text (no JSON wrapping needed).

ALTERNATIVES (may be empty):
{alternatives_text}
""",
)

GOAL_PERSONALISE = Prompt(
    name="goal.personalise",
    version="1.0.0",
    template="""You are a personal financial mentor. Given the following goal
evaluation, write 2-3 personalised talking points the user should keep in mind.

Goal evaluation JSON (deterministic, do NOT recalculate):
{{
  "target": 80000,
  "months": 8,
  "income": 35000,
  "expenses": 25000,
  "current_savings": 0,
  "required_monthly": 10000,
  "savings_ratio_percent": 28.6,
  "status": "stretch",
  "feasibility_message": "Stretch goal: Saving 10000.00 per month (28.6% of your income) over 8 months will reach your goal.",
  "budget_adjustments": [
    {{"category": "Discretionary", "current_spend": 12500.0, "suggested_reduction": 5000.0, "new_spend": 7500.0}}
  ],
  "alternatives": [
    {{"option": "extend_timeline", "new_monthly": 5000, "new_timeline_months": 16, "monthly_reduction_pct": 50.0, "status": "feasible"}}
  ]
}}"""

)


# ---------------------------------------------------------------------------
# Helper: format alternatives list for the prompt
# ---------------------------------------------------------------------------

def _format_alternatives(alternatives: List[Dict[str, Any]]) -> str:
    """Format the alternatives list into a prompt-friendly string."""
    if not alternatives:
        return "(none)"
    lines: list[str] = []
    for i, alt in enumerate(alternatives, 1):
        option = alt.get("option", "unknown")
        if option == "extend_timeline":
            lines.append(
                f"{i}. Extend timeline to {alt['new_timeline_months']} months; "
                f"new monthly savings {alt['new_monthly']:.0f}. "
                f"Monthly reduction {alt['monthly_reduction_pct']:.0f}%."
            )
        elif option == "reduce_target":
            lines.append(
                f"{i}. Reduce target to ₹{alt['new_target']:.0f} "
                f"(-{alt['reduction_pct']:.0f}%); new monthly {alt['new_monthly']:.0f}."
            )
        elif option == "partial_down_payment":
            lines.append(
                f"{i}. Partial down payment of ₹{alt['new_target']:.0f}; "
                f"remaining ₹{alt['remaining_balance']:.0f} after {months} months, "
                f"monthly {alt['new_monthly']:.0f}."
            )
        elif option == "accept_lower_progress":
            lines.append(
                f"{i}. Save at {alt['new_monthly']:.0f} per month toward "
                f"₹{alt['new_target']:.0f} ({(alt['progress_pct']):.0f}% of original target)."
            )
        else:
            lines.append(f"{i}. {option}: {alt}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------------


def explain_goal(
    plan: SavingsPlan,
    *,
    user_question: str = "",
    include_alternatives: bool = True,
    client: Optional[LLMClient] = None,
) -> Dict[str, str]:
    """Run the LLM explanation layer for a goal evaluation.

    Returns a dict with:
        - "explanation": the LLM-generated plain-text explanation, or the
          deterministic fallback if the LLM is unavailable.
        - "engine": "llm" or "fallback" indicating which path was taken.

    The deterministic fallback is constructed from the plan object and is
    guaranteed to use only the plan's numbers – it never recalculates.
    """
    cclient = client or get_client()

    # Build alternatives text for the prompt
    alternatives_text = _format_alternatives(plan.alternatives) if include_alternatives else ""

    # Render the prompt with all plan data
    prompt_template = GOAL_EXPLAIN.render(
        target=plan.required_monthly * plan.months_to_goal if plan.months_to_goal else 0,
        months=plan.months_to_goal or 8,
        income=plan.available_surplus * Decimal("2") if plan.available_surplus else 0,
        current_savings=plan.recommended_monthly or Decimal("0"),
        expenses=plan.available_surplus * Decimal("0.8") if plan.available_surplus else 0,
        required_monthly=plan.required_monthly,
        savings_ratio_percent=float(plan.savings_ratio * Decimal("100")),
        status=plan.status.value,
        feasibility_message=plan.feasibility_message,
        user_question=user_question,
        alternatives_text=alternatives_text,
    )

    try:
        resp = cclient.complete(
            [{"role": "user", "content": prompt_template}],
            temperature=SETTINGS.temperature_summarise,
            max_tokens=600,
            seed=SETTINGS.seed,
        )
        explanation = resp.content.strip()
        return {"explanation": explanation, "engine": "llm"}
    except (LLMUnavailableError, Exception) as err:
        log.warning("LLM explanation failed (%s); using fallback: %s", err, err)
        # Deterministic fallback – never recalculates, only interprets plan data
        fallback = _deterministic_fallback(plan, user_question, plan.alternatives)
        return {"explanation": fallback, "engine": "fallback"}


def personalise_recommendations(
    plan: SavingsPlan,
    *,
    client: Optional[LLMClient] = None,
) -> Dict[str, str]:
    """Ask the LLM to produce 2-3 personalised talking points for the user.

    Returns a dict with:
        - "talking_points": the LLM-generated text, or a deterministic fallback.
        - "engine": "llm" or "fallback".
    """
    cclient = client or get_client()

    alternatives_text = _format_alternatives(plan.alternatives)

    prompt_template = GOAL_PERSONALISE.render(
        target=plan.required_monthly * plan.months_to_goal if plan.months_to_goal else 0,
        months=plan.months_to_goal or 8,
        income=plan.available_surplus * Decimal("2") if plan.available_surplus else 0,
        current_savings=plan.recommended_monthly or Decimal("0"),
        expenses=plan.available_surplus * Decimal("0.8") if plan.available_surplus else 0,
        required_monthly=plan.required_monthly,
        savings_ratio_percent=float(plan.savings_ratio * Decimal("100")),
        status=plan.status.value,
        feasibility_message=plan.feasibility_message,
        alternatives_text=alternatives_text,
    )

    try:
        resp = cclient.complete(
            [{"role": "user", "content": prompt_template}],
            temperature=SETTINGS.temperature_summarise,
            max_tokens=400,
            seed=SETTINGS.seed,
        )
        talking_points = resp.content.strip()
        return {"talking_points": talking_points, "engine": "llm"}
    except (LLMUnavailableError, Exception) as err:
        log.warning("LLM personalisation failed (%s); using fallback: %s", err, err)
        fallback = _deterministic_personalisation(plan)
        return {"talking_points": fallback, "engine": "fallback"}


def _deterministic_fallback(
    plan: SavingsPlan,
    user_question: str,
    alternatives: bool,
) -> str:
    """Build a fallback explanation using only the plan's numbers.

    This is the "guaranteed" path – the LLM is not called, so the output
    is completely deterministic and never changes the calculated numbers.
    """
    status_label = plan.status.value
    ratio_pct = float(plan.savings_ratio * Decimal("100"))
    required = plan.required_monthly

    lines: list[str] = []

    # Core assessment
    if status_label == "feasible":
        lines.append(
            f"Your goal is <b>feasible</b>. To reach ₹{plan.required_monthly * plan.months_to_goal if plan.months_to_goal else 0:,.2f}"
            f" over {plan.months_to_goal or 8} months, you need to save ₹{required:,.2f} per month."
        )
    elif status_label == "stretch":
        lines.append(
            f"This is a <b>stretch goal</b>. Saving ₹{required:,.2f} per month "
            f"({ratio_pct:.1f}% of your income) over {plan.months_to_goal or 8} months "
            f"is possible with careful budgeting."
        )
    else:
        lines.append(
            f"Achieving this goal within {plan.months_to_goal or 8} months is <b>challenging</b>. "
            f"Saving ₹{required:,.2f} per month ({ratio_pct:.1f}% of your income) "
            f"exceeds typical guidelines."
        )

    # User question context
    if user_question:
        lines.append(f"Regarding your question: {user_question}")

    # Alternatives summary
    if alternatives and plan.alternatives:
        lines.append("Alternative strategies to consider:")
        for alt in plan.alternatives[:3]:
            option = alt.get("option", "unknown")
            if option == "extend_timeline":
                lines.append(
                    f"• Extend the timeline to {alt['new_timeline_months']} months, "
                    f"reducing your monthly savings requirement."
                )
            elif option == "reduce_target":
                lines.append(
                    f"• Reduce the target amount – aiming for a smaller goal "
                    f"within the original timeline."
                )
            elif option == "partial_down_payment":
                lines.append(
                    f"• Start with a partial down payment of ₹{alt['new_target']:,.0f}, "
                    f"then save for the remainder later."
                )
            elif option == "accept_lower_progress":
                lines.append(
                    f"• Save ₹{alt['new_monthly']:,.0f} per month toward "
                    f"₹{alt['new_target']:,.0f} ({(alt['progress_pct']):.0f}% of the original target)."
                )

    # Clear next step
    lines.append(
        "Next step: Review your monthly budget and identify discretionary "
        "expenses you can trim, or consider extending your timeline."
    )

    return "\n".join(lines)


def _deterministic_personalisation(plan: SavingsPlan) -> str:
    """Build a deterministic personalisation fallback.

    Uses only the plan's pre-computed numbers – no recalculation.
    """
    status_label = plan.status.value
    ratio_pct = float(plan.savings_ratio * Decimal("100"))
    required = plan.required_monthly
    months = plan.months_to_goal or 8

    points: list[str] = []

    if status_label == "feasible":
        points.append(
            f"Saving ₹{required:,.2f} monthly ({ratio_pct:.1f}% of income) is comfortably "
            f"within the 20% guideline – you can reach your goal on schedule."
        )
    elif status_label == "stretch":
        points.append(
            f"At ₹{required:,.2f} monthly ({ratio_pct:.1f}% of income), this is a stretch "
            f"but achievable with discipline. Track your spending weekly."
        )
    else:
        points.append(
            f"Saving ₹{required:,.2f} monthly ({ratio_pct:.1f}% of income) is above the "
            f"40% threshold – consider extending your timeline or reducing the target."
        )

    points.append(
        "Tip: Review discretionary categories (dining, subscriptions, entertainment) "
        "for areas to trim."
    )

    if plan.budget_adjustments:
        adj = plan.budget_adjustments[0]
        points.append(
            f"Consider reducing {adj['category']} spending by ₹{adj['suggested_reduction']:,.2f} "
            f"per month to free up savings."
        )

    return "\n".join(points)