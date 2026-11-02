"""Deterministic financial goal recommendation engine.

All calculations use :class:`decimal.Decimal` for exact arithmetic.
Feasibility thresholds are configurable constants.

Public API:
    - required_monthly_savings
    - assess_feasibility
    - estimate_time_to_goal
    - suggest_budget_adjustments
    - generate_alternatives
    - evaluate_goal
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional


class GoalStatus(Enum):
    FEASIBLE = "feasible"
    STRETCH = "stretch"
    NOT_FEASIBLE = "not_feasible"


#: Maximum savings ratio (as fraction of income) that is comfortably achievable.
#: Users saving up to this % of income can reasonably meet the goal.
COMFORTABLE_RATIO: Decimal = Decimal("0.20")

#: Savings ratio range that is achievable but requires discipline (a "stretch").
#: Goals requiring 20–40% of income are possible with careful budgeting.
STRETCH_RATIO_MAX: Decimal = Decimal("0.40")

#: Savings ratio above which a goal is considered not feasible given typical
#: income/expense constraints.
NOT_FEASIBLE_RATIO: Decimal = Decimal("0.50")


@dataclass
class SavingsPlan:
    """Structured result from goal evaluation."""

    required_monthly: Decimal
    available_surplus: Decimal
    savings_ratio: Decimal
    status: GoalStatus
    months_to_goal: int
    feasibility_message: str
    recommended_monthly: Decimal = field(default=None)
    budget_adjustments: List[Dict[str, Any]] = field(default_factory=list)
    alternatives: List[Dict[str, Any]] = field(default_factory=list)


def _round(value: Decimal, places: int = 2) -> Decimal:
    """Round a Decimal to two decimal places (currency precision)."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def required_monthly_savings(
    target: Decimal,
    months: int,
    current_savings: Decimal = Decimal("0"),
    expected_return: Decimal = Decimal("0"),
) -> Decimal:
    """Calculate the required monthly savings to reach a target.

    Formula: (target - current_savings - expected_return_earned) / months
    expected_return_earned is simple interest: current_savings * expected_return * months/12

    Returns a Decimal rounded to 2 decimal places.
    """
    if months <= 0:
        raise ValueError("months must be a positive integer")
    target = Decimal(str(target))
    current = Decimal(str(current_savings))
    erate = Decimal(str(expected_return))

    # Subtract existing savings
    remaining = target - current
    if remaining <= 0:
        return Decimal("0.00")

    # Subtract simple interest earned on existing savings
    if erate > 0:
        interest_earned = (current * erate * Decimal(months) / Decimal("12")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        remaining -= interest_earned
        if remaining <= 0:
            return Decimal("0.00")

    monthly = remaining / Decimal(months)
    return _round(monthly)


def assess_feasibility(
    required: Decimal,
    income: Decimal,
    expenses: Decimal,
) -> GoalStatus:
    """Determine whether a goal is feasible given income and expenses.

    The savings ratio is *required* divided by *income*.

    - ratio <= 0.20       -> FEASIBLE
    - 0.20 < ratio <= 0.40 -> STRETCH
    - ratio > 0.40       -> NOT_FEASIBLE

    Additionally, if the required amount exceeds the actual monthly surplus
    (income - expenses), the goal is marked NOT_FEASIBLE regardless of the ratio.
    """
    income = Decimal(str(income))
    expenses = Decimal(str(expenses))
    surplus = income - expenses

    if income <= 0:
        return GoalStatus.NOT_FEASIBLE

    required = Decimal(str(required))
    ratio = required / income

    # If required exceeds actual surplus, it's not feasible
    if required > surplus:
        return GoalStatus.NOT_FEASIBLE

    if ratio <= COMFORTABLE_RATIO:
        return GoalStatus.FEASIBLE
    if ratio <= STRETCH_RATIO_MAX:
        return GoalStatus.STRETCH
    return GoalStatus.NOT_FEASIBLE


def estimate_time_to_goal(
    target: Decimal,
    monthly_savings: Decimal,
    current_savings: Decimal = Decimal("0"),
) -> int:
    """Estimate the number of months needed to reach a goal.

    Returns 0 if the goal is already met or exceeded.
    """
    target = Decimal(str(target))
    current = Decimal(str(current_savings))
    if current >= target:
        return 0
    remaining = target - current
    if monthly_savings <= 0:
        return 999_999  # sentinel for "unclear"
    months = (remaining / Decimal(monthly_savings)).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(months)


def suggest_budget_adjustments(
    expenses_by_category: Dict[str, Decimal],
    gap: Decimal,
) -> List[Dict[str, Any]]:
    """Suggest which discretionary categories to trim to cover a savings gap.

    Categories are sorted by spend (highest first) and recommendations are
    generated to trim enough to cover *gap*. Only discretionary categories
    (those with spend > 0) are considered; the user can decide what is
    discretionary vs. necessary.

    Returns a list of dicts with ``category``, ``current_spend``,
    ``suggested_reduction``, and ``new_spend``.
    """
    if gap <= 0:
        return []

    # Sort categories by spend descending so we recommend trimming the largest
    # discretionary items first.
    sorted_cats = sorted(
        expenses_by_category.items(), key=lambda item: item[1], reverse=True
    )

    recommendations: List[Dict[str, Any]] = []
    remaining_gap = Decimal(str(gap))

    for category, spend in sorted_cats:
        if spend <= 0 or remaining_gap <= 0:
            continue
        # Suggest reducing this category by up to 50% or enough to cover the gap, whichever is less
        max_reduction = min(spend / Decimal("2"), remaining_gap)
        reduction = max_reduction.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        new_spend = (spend - reduction).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        recommendations.append(
            {
                "category": category,
                "current_spend": float(spend),
                "suggested_reduction": float(reduction),
                "new_spend": float(new_spend),
            }
        )
        remaining_gap -= reduction

    return recommendations


def generate_alternatives(
    target: Decimal,
    months: int,
    income: Decimal,
    current_savings: Decimal = Decimal("0"),
    expected_return: Decimal = Decimal("0"),
) -> list[dict[str, Any]]:
    """Generate alternative strategies when the original goal is not feasible.

    Alternatives considered (in order of preference):
      1. Extend the timeline
      2. Reduce the target amount
      3. Make a partial down payment / start with a cheaper option
      4. Reduce monthly savings target and accept longer time

    Each alternative is a dict with keys describing the option and the
    new required monthly savings.
    """
    inc = Decimal(str(income))
    cur = Decimal(str(current_savings))
    target = Decimal(str(target))
    months = int(months)

    alternatives: List[Dict[str, Any]] = []

    # 1. Extend timeline – keep target, find monthly savings for new longer period
    for ext_months in [months * 2, months * 3, months * 4]:
        new_monthly = required_monthly_savings(target, ext_months, cur, expected_return)
        ratio = new_monthly / inc
        status = (
            GoalStatus.FEASIBLE
            if ratio <= COMFORTABLE_RATIO
            else GoalStatus.STRETCH if ratio <= STRETCH_RATIO_MAX
            else GoalStatus.NOT_FEASIBLE
        )
        if status != GoalStatus.NOT_FEASIBLE:
            alternatives.append(
                {
                    "option": "extend_timeline",
                    "new_monthly": float(_round(new_monthly)),
                    "new_timeline_months": ext_months,
                    "monthly_reduction_pct": round(
                        (1 - new_monthly / required_monthly_savings(target, months, cur, expected_return))
                        * 100,
                        1,
                    ),
                    "status": status.value,
                }
            )

    # 2. Reduce target – keep timeline, find smaller target that fits the original monthly budget
    #    Use 75% of original target as a starting point for reduction
    reduced_target = (target * Decimal("0.75")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    new_monthly_reduced = required_monthly_savings(reduced_target, months, cur, expected_return)
    ratio_reduced = new_monthly_reduced / inc
    status_reduced = (
        GoalStatus.FEASIBLE
        if ratio_reduced <= COMFORTABLE_RATIO
        else GoalStatus.STRETCH if ratio_reduced <= STRETCH_RATIO_MAX
        else GoalStatus.NOT_FEASIBLE
    )
    if status_reduced != GoalStatus.NOT_FEASIBLE:
        alternatives.append(
            {
                "option": "reduce_target",
                "new_target": float(_round(reduced_target)),
                "new_monthly": float(_round(new_monthly_reduced)),
                "reduction_pct": 25.0,
                "status": status_reduced.value,
            }
        )

    # 3. Partial down payment – start with a smaller immediate goal
    partial = (target * Decimal("0.5")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    new_monthly_partial = required_monthly_savings(partial, months, cur, expected_return)
    ratio_partial = new_monthly_partial / inc
    status_partial = (
        GoalStatus.FEASIBLE
        if ratio_partial <= COMFORTABLE_RATIO
        else GoalStatus.STRETCH if ratio_partial <= STRETCH_RATIO_MAX
        else GoalStatus.NOT_FEASIBLE
    )
    if status_partial != GoalStatus.NOT_FEASIBLE:
        alternatives.append(
            {
                "option": "partial_down_payment",
                "new_target": float(_round(partial)),
                "new_monthly": float(_round(new_monthly_partial)),
                "remaining_balance": float(_round(target - partial)),
                "status": status_partial.value,
            }
        )

    # 4. Reduce monthly savings target – accept longer time to goal
    #    Keep original target and timeline, just lower the bar on what "success" means
    #    e.g., success = saving 75% of target within the original timeline
    success_target = (target * Decimal("0.75")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    new_monthly_accept = required_monthly_savings(success_target, months, cur, expected_return)
    ratio_accept = new_monthly_accept / inc
    status_accept = (
        GoalStatus.FEASIBLE
        if ratio_accept <= COMFORTABLE_RATIO
        else GoalStatus.STRETCH if ratio_accept <= STRETCH_RATIO_MAX
        else GoalStatus.NOT_FEASIBLE
    )
    if status_accept != GoalStatus.NOT_FEASIBLE:
        alternatives.append(
            {
                "option": "accept_lower_progress",
                "new_target": float(_round(success_target)),
                "new_monthly": float(_round(new_monthly_accept)),
                "progress_pct": 75.0,
                "status": status_accept.value,
            }
        )

    return alternatives


def evaluate_goal(
    target: Decimal,
    months: int,
    income: Decimal,
    expenses: Decimal,
    current_savings: Decimal = Decimal("0"),
    expected_return: Decimal = Decimal("0"),
) -> SavingsPlan:
    """Full evaluation of a financial goal.

    Returns a :class:`SavingsPlan` dataclass with all computed values and a
    human‑readable feasibility message.
    """
    required = required_monthly_savings(target, months, current_savings, expected_return)
    status = assess_feasibility(required, income, expenses)
    months_to_goal = estimate_time_to_goal(target, required, current_savings)

    # Build feasibility message
    if status == GoalStatus.FEASIBLE:
        feasibility_message = (
            f"Achievable! Saving {required:.2f} per month "
            f"({required / income * Decimal('100'):.1f}% of your income) "
            f"over {months} months will reach your goal."
        )
    elif status == GoalStatus.STRETCH:
        feasibility_message = (
            f"Stretch goal: Saving {required:.2f} per month "
            f"({required / income * Decimal('100'):.1f}% of your income) "
            f"over {months} months is possible with careful budgeting."
        )
    else:
        feasibility_message = (
            f"Challenging: Saving {required:.2f} per month "
            f"({required / income * Decimal('100'):.1f}% of your income) "
            f"over {months} months exceeds typical guidelines. "
            "Consider alternatives below."
        )

    # Budget adjustments based on the gap between income and expenses
    surplus = income - expenses
    gap = required - surplus if required > surplus else Decimal("0")

    budget_adjustments = suggest_budget_adjustments(
        {"Essential": expenses * Decimal("0.5"), "Discretionary": expenses * Decimal("0.5")},
        gap,
    )

    alternatives = generate_alternatives(
        target, months, income, current_savings, expected_return
    )

    recommended_monthly = required if status in (GoalStatus.FEASIBLE, GoalStatus.STRETCH) else Decimal("0")

    return SavingsPlan(
        required_monthly=required,
        available_surplus=surplus,
        savings_ratio=required / income if income > 0 else Decimal("0"),
        status=status,
        months_to_goal=months_to_goal,
        feasibility_message=feasibility_message,
        recommended_monthly=recommended_monthly,
        budget_adjustments=budget_adjustments,
        alternatives=alternatives,
    )