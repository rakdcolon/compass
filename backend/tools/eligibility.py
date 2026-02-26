"""
Benefit eligibility checking tool.
Determines which federal programs a user likely qualifies for based on their situation.
"""

from typing import Any
from backend.config import get_fpl
from backend.data.benefits_db import BENEFITS_PROGRAMS


def check_benefit_eligibility(
    annual_income: float,
    household_size: int,
    state: str,
    age: int,
    employment_status: str,
    special_circumstances: list[str],
) -> dict[str, Any]:
    """
    Check eligibility for major federal benefit programs.

    Args:
        annual_income: Gross annual household income in dollars
        household_size: Number of people in the household
        state: Two-letter state abbreviation or full state name
        age: Age of the primary applicant
        employment_status: 'employed', 'unemployed', 'self_employed', 'retired', 'disabled'
        special_circumstances: List from ['disabled', 'pregnant', 'infant_child', 'veteran',
                                          'elderly', 'domestic_violence', 'homeless', 'student']

    Returns:
        dict with 'eligible_programs', 'potentially_eligible', and 'summary'
    """
    fpl = get_fpl(household_size)
    income_pct_fpl = (annual_income / fpl * 100) if fpl > 0 else 999
    monthly_income = annual_income / 12

    eligible = []
    potentially_eligible = []

    # -- SNAP --
    snap_limit = 130  # default; many states have categorical eligibility up to 200%
    if income_pct_fpl <= snap_limit:
        eligible.append(_build_result(
            "snap",
            "High",
            _estimate_snap_benefit(household_size, annual_income),
            "Income is within SNAP gross limit (130% FPL)",
        ))
    elif income_pct_fpl <= 200:
        potentially_eligible.append(_build_result(
            "snap",
            "Medium",
            _estimate_snap_benefit(household_size, annual_income),
            "May qualify through categorical/broad-based eligibility in many states",
        ))

    # -- Medicaid --
    is_expansion_state = _is_medicaid_expansion_state(state)
    medicaid_limit = 138 if is_expansion_state else 65
    if income_pct_fpl <= medicaid_limit:
        eligible.append(_build_result(
            "medicaid",
            "High",
            "Comprehensive health coverage",
            f"Income qualifies for Medicaid in {'expansion' if is_expansion_state else 'your'} state",
        ))
    elif "pregnant" in special_circumstances and income_pct_fpl <= 220:
        eligible.append(_build_result(
            "medicaid",
            "High",
            "Full pregnancy & postpartum coverage",
            "Pregnant women covered at higher income levels in all states",
        ))
    elif income_pct_fpl <= 250:
        potentially_eligible.append(_build_result(
            "medicaid",
            "Low",
            "Varies by state",
            "Check your state's specific Medicaid income limits",
        ))

    # -- CHIP --
    has_young_children = "infant_child" in special_circumstances or any(
        c in special_circumstances for c in ["child_under_5", "child_under_19"]
    )
    if household_size >= 2 and income_pct_fpl <= 200:
        eligible.append(_build_result(
            "chip",
            "High" if income_pct_fpl <= 150 else "Medium",
            "Low-cost health coverage for children",
            "Children up to age 19 may qualify for CHIP",
        ))
    elif household_size >= 2 and income_pct_fpl <= 300:
        potentially_eligible.append(_build_result(
            "chip",
            "Medium",
            "Low-cost health coverage for children",
            "Many states cover children up to 300% FPL",
        ))

    # -- TANF --
    has_children = household_size >= 2 and (
        "infant_child" in special_circumstances or household_size > 1
    )
    if has_children and income_pct_fpl <= 60:
        eligible.append(_build_result(
            "tanf",
            "High",
            _estimate_tanf_benefit(household_size, state),
            "Families with children and very low income may qualify for cash assistance",
        ))
    elif has_children and income_pct_fpl <= 100:
        potentially_eligible.append(_build_result(
            "tanf",
            "Medium",
            _estimate_tanf_benefit(household_size, state),
            "May qualify depending on your state's income limits and work requirements",
        ))

    # -- WIC --
    wic_eligible = (
        "pregnant" in special_circumstances
        or "infant_child" in special_circumstances
        or age <= 40  # proxy for having young children
    )
    if wic_eligible and income_pct_fpl <= 185:
        eligible.append(_build_result(
            "wic",
            "High",
            "$50–$75/month in food vouchers + nutrition support",
            "Eligible for pregnant women, new mothers, and children under 5",
        ))

    # -- LIHEAP --
    if income_pct_fpl <= 150:
        priority = "High" if (age >= 60 or "disabled" in special_circumstances) else "Medium"
        eligible.append(_build_result(
            "liheap",
            priority,
            "$400–$600/year toward energy bills",
            "Helps cover heating/cooling costs; priority for elderly and disabled",
        ))
    elif income_pct_fpl <= 200:
        potentially_eligible.append(_build_result(
            "liheap",
            "Low",
            "$200–$400/year",
            "Some states have higher income limits; check your local office",
        ))

    # -- SSI --
    if ("disabled" in special_circumstances or age >= 65) and annual_income <= 20000:
        eligible.append(_build_result(
            "ssi",
            "High" if annual_income <= 10000 else "Medium",
            f"Up to $943/month (2024 federal rate)",
            "Available for disabled or elderly individuals with limited income and resources",
        ))

    # -- Section 8 / Housing --
    if income_pct_fpl <= 80:  # 80% AMI is HUD eligibility; 50% is typical
        priority = "High" if income_pct_fpl <= 30 or "homeless" in special_circumstances else "Medium"
        eligible.append(_build_result(
            "section8",
            priority,
            "Pays rent above 30% of your income",
            "Waitlists are common but worth applying; homeless/disabled get priority",
        ))

    # -- EITC --
    if employment_status in ("employed", "self_employed") and income_pct_fpl <= 350:
        max_eitc = _estimate_eitc(annual_income, household_size)
        if max_eitc > 0:
            eligible.append(_build_result(
                "eitc",
                "High",
                f"Up to ${max_eitc:,} when you file taxes",
                "Refundable tax credit — file a return to claim even if you owe no taxes",
            ))

    # -- Medicare Savings Programs --
    if age >= 65 and income_pct_fpl <= 135:
        eligible.append(_build_result(
            "medicare_savings",
            "High",
            "$2,000–$5,000/year in saved Medicare costs",
            "Can eliminate Medicare premiums and cost-sharing",
        ))

    # Build summary
    total_est_monthly = _total_monthly_estimate(eligible)

    return {
        "eligible_programs": eligible,
        "potentially_eligible": potentially_eligible,
        "total_programs_found": len(eligible) + len(potentially_eligible),
        "estimated_monthly_value": total_est_monthly,
        "income_pct_fpl": round(income_pct_fpl, 1),
        "fpl_threshold": fpl,
        "summary": (
            f"Based on your income of ${annual_income:,.0f}/year for a household of {household_size}, "
            f"you are at {income_pct_fpl:.0f}% of the Federal Poverty Level. "
            f"You likely qualify for {len(eligible)} program(s) and may qualify for "
            f"{len(potentially_eligible)} additional program(s). "
            f"Estimated combined value: ${total_est_monthly:,.0f}/month."
        ),
    }


def _build_result(program_id: str, likelihood: str, estimated_value: str, reason: str) -> dict:
    from backend.data.benefits_db import BENEFITS_BY_ID
    program = BENEFITS_BY_ID.get(program_id, {})
    return {
        "id": program_id,
        "name": program.get("name", program_id),
        "short_name": program.get("short_name", program_id),
        "category": program.get("category", "other"),
        "likelihood": likelihood,
        "estimated_value": estimated_value,
        "reason": reason,
        "apply_url": program.get("apply_url", ""),
        "how_to_apply": program.get("how_to_apply", ""),
        "timeline": program.get("timeline", ""),
    }


def _estimate_snap_benefit(household_size: int, annual_income: float) -> str:
    # 2024 max SNAP allotments
    max_allotments = {1: 291, 2: 535, 3: 766, 4: 973, 5: 1155, 6: 1386, 7: 1532, 8: 1751}
    max_benefit = max_allotments.get(min(household_size, 8), 1751 + (household_size - 8) * 200)
    monthly_income = annual_income / 12
    net_income = max(0, monthly_income * 0.7)  # 30% deduction approximation
    calculated = max(0, max_benefit - (net_income * 0.3))
    return f"~${int(calculated):,}/month (up to ${max_benefit:,}/month maximum)"


def _estimate_tanf_benefit(household_size: int, state: str) -> str:
    # Average TANF by family size — varies enormously by state
    estimates = {1: 250, 2: 380, 3: 447, 4: 520, 5: 590}
    est = estimates.get(min(household_size, 5), 590)
    return f"~${est}/month (varies significantly by state)"


def _estimate_eitc(annual_income: float, household_size: int) -> int:
    # 2024 EITC maximum credit amounts
    max_credits = {0: 632, 1: 4213, 2: 6960}
    children = max(0, min(household_size - 1, 3))
    max_credit = max_credits.get(min(children, 2), 7830)
    # Simplified phase-in/phase-out
    if annual_income < 10000:
        return int(max_credit * 0.6)
    elif annual_income < 20000:
        return max_credit
    elif annual_income < 30000:
        return int(max_credit * 0.7)
    else:
        return int(max_credit * 0.3)


def _total_monthly_estimate(eligible: list) -> int:
    """Very rough estimate for the summary statement."""
    total = 0
    for p in eligible:
        val = p.get("estimated_value", "")
        if "month" in val.lower():
            import re
            nums = re.findall(r"\$?([\d,]+)", val)
            if nums:
                try:
                    total += int(nums[0].replace(",", ""))
                except ValueError:
                    pass
    return total


def _is_medicaid_expansion_state(state: str) -> bool:
    """Returns True if the state expanded Medicaid under the ACA."""
    expansion_states = {
        "AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DC", "DE", "HI",
        "IA", "ID", "IL", "IN", "KY", "LA", "MA", "MD", "ME", "MI",
        "MN", "MO", "MS", "MT", "ND", "NE", "NH", "NJ", "NM", "NV",
        "NY", "OH", "OK", "OR", "PA", "RI", "SD", "UT", "VA", "VT",
        "WA", "WI", "WV",
    }
    state_upper = state.upper().strip()
    # Handle full names too
    name_to_abbr = {
        "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
        "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE",
        "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI", "IDAHO": "ID",
        "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
        "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
        "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS",
        "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
        "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM", "NEW YORK": "NY",
        "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
        "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC",
        "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT",
        "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA", "WEST VIRGINIA": "WV",
        "WISCONSIN": "WI", "WYOMING": "WY", "DISTRICT OF COLUMBIA": "DC",
    }
    abbr = name_to_abbr.get(state_upper, state_upper)
    return abbr in expansion_states
