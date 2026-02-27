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

    # -- SSDI --
    if "disabled" in special_circumstances and employment_status == "disabled":
        eligible.append(_build_result(
            "ssdi",
            "High",
            "~$1,537/month average (based on work history)",
            "Workers with a qualifying disability who paid Social Security taxes may receive SSDI",
        ))
    elif "disabled" in special_circumstances:
        potentially_eligible.append(_build_result(
            "ssdi",
            "Medium",
            "Up to $3,822+/month depending on work history",
            "If you cannot work due to disability, you may qualify for SSDI based on your work record",
        ))

    # -- Unemployment Insurance --
    if employment_status == "unemployed" and annual_income < 80000:
        eligible.append(_build_result(
            "unemployment_insurance",
            "High",
            "~40-50% of prior wages; average ~$440/week for up to 26 weeks",
            "Recently unemployed workers may qualify — apply immediately after job loss",
        ))

    # -- Extra Help (Medicare Part D LIS) --
    if (age >= 65 or "disabled" in special_circumstances) and income_pct_fpl <= 150:
        eligible.append(_build_result(
            "extra_help",
            "High",
            "Up to $5,900/year in prescription drug savings",
            "Medicare beneficiaries with low income can get Extra Help for drug costs",
        ))
    elif (age >= 65 or "disabled" in special_circumstances) and income_pct_fpl <= 185:
        potentially_eligible.append(_build_result(
            "extra_help",
            "Medium",
            "Partial subsidy for prescription drug costs",
            "Income is near the Extra Help limit — apply to determine exact eligibility",
        ))

    # -- National School Lunch Program --
    if household_size >= 2 and income_pct_fpl <= 185:
        eligible.append(_build_result(
            "nslp",
            "High" if income_pct_fpl <= 130 else "Medium",
            "Free ($3.50/day) or reduced-price ($0.40/day) school lunch per child",
            "School-age children qualify for free/reduced school meals based on household income",
        ))

    # -- CCDF (Child Care Subsidy) --
    has_young_child = "infant_child" in special_circumstances or (household_size >= 2 and age <= 50)
    if has_young_child and income_pct_fpl <= 200 and employment_status in ("employed", "self_employed", "student"):
        eligible.append(_build_result(
            "ccdf",
            "High" if income_pct_fpl <= 130 else "Medium",
            "Covers majority of child care costs; subsidy worth $400–$1,200/month",
            "Working families with children under 13 may qualify for child care assistance",
        ))
    elif has_young_child and income_pct_fpl <= 250:
        potentially_eligible.append(_build_result(
            "ccdf",
            "Low",
            "Partial child care subsidy based on income",
            "Check your state's CCDF income limit — some states cover higher incomes",
        ))

    # -- Lifeline Phone/Internet --
    if income_pct_fpl <= 135:
        eligible.append(_build_result(
            "lifeline",
            "High",
            "$9.25/month discount on phone or internet (~$111/year)",
            "Low-income households qualify for a monthly phone or internet discount",
        ))

    # -- Head Start --
    if "infant_child" in special_circumstances and income_pct_fpl <= 130:
        eligible.append(_build_result(
            "head_start",
            "High",
            "Free early childhood education worth $10,000–$20,000/year per child",
            "Low-income families with children under 5 may enroll in Head Start",
        ))
    elif "infant_child" in special_circumstances and income_pct_fpl <= 185:
        potentially_eligible.append(_build_result(
            "head_start",
            "Medium",
            "Free preschool and family support services",
            "Some Head Start slots available for slightly higher incomes — contact your local program",
        ))

    # -- Weatherization Assistance --
    if income_pct_fpl <= 200:
        priority = "High" if (age >= 60 or "disabled" in special_circumstances or household_size >= 3) else "Medium"
        eligible.append(_build_result(
            "weatherization",
            priority,
            "Free home improvements worth $5,000–$6,500; saves ~$283/year on energy bills",
            "Low-income households qualify for free weatherization to reduce energy costs",
        ))

    # -- Veterans programs --
    state_abbr = _get_state_abbr(state)
    if "veteran" in special_circumstances:
        if "disabled" in special_circumstances:
            eligible.append(_build_result(
                "va_disability",
                "High",
                "Tax-free monthly payment; $171–$3,831+/month depending on rating",
                "Veterans with service-connected disabilities may receive tax-free monthly compensation",
            ))
        if (age >= 65 or "disabled" in special_circumstances) and annual_income < 30000:
            eligible.append(_build_result(
                "va_pension",
                "High" if annual_income < 20000 else "Medium",
                "Up to $1,254/month; up to $3,261/month with Aid & Attendance",
                "Low-income wartime veterans (65+ or disabled) may qualify for VA Pension",
            ))

    # -- Emergency Rental Assistance --
    if "homeless" in special_circumstances or income_pct_fpl <= 80:
        eligible.append(_build_result(
            "emergency_rental",
            "High" if "homeless" in special_circumstances else "Medium",
            "Up to 12-18 months of rent and utility assistance",
            "Low-income households facing housing instability may qualify for emergency rental help",
        ))
    elif income_pct_fpl <= 120:
        potentially_eligible.append(_build_result(
            "emergency_rental",
            "Low",
            "Short-term rental assistance if facing eviction risk",
            "Call 2-1-1 to check local program availability and income limits",
        ))

    # -- State EITC (multi-state) --
    STATE_EITC_STATES = {
        "CA", "CO", "CT", "DC", "DE", "HI", "IA", "IL", "IN", "KS",
        "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MT", "NE", "NJ",
        "NM", "NY", "OH", "OK", "OR", "RI", "SC", "TX", "VA", "VT",
        "WA", "WI",
    }
    if (
        employment_status in ("employed", "self_employed")
        and state_abbr in STATE_EITC_STATES
        and income_pct_fpl <= 350
        and _estimate_eitc(annual_income, household_size) > 0
        and state_abbr not in ("CA", "NY", "WA")  # handled separately below
    ):
        eitc_est = _estimate_eitc(annual_income, household_size)
        state_pct = {"CO": 25, "CT": 30.5, "DC": 40, "IL": 20, "MA": 30, "MD": 45,
                     "ME": 25, "MI": 6, "MN": 63, "NJ": 40, "NY": 30, "OR": 9,
                     "VT": 38, "WI": 4}.get(state_abbr, 15)
        state_est = int(eitc_est * state_pct / 100)
        if state_est > 0:
            potentially_eligible.append(_build_result(
                "state_eitc",
                "High",
                f"~${state_est:,} additional (≈{state_pct}% of federal EITC) at tax time",
                f"Your state offers a state EITC worth ~{state_pct}% of your federal EITC credit",
            ))

    # -- California-specific --
    if state_abbr == "CA":
        if employment_status in ("employed", "self_employed") and annual_income <= 30931:
            caleitc_est = _estimate_caleitc(annual_income, household_size)
            if caleitc_est > 0:
                eligible.append(_build_result(
                    "caleitc",
                    "High",
                    f"Up to ${caleitc_est:,} at tax time (CalEITC + Young Child Tax Credit if applicable)",
                    "California workers with low income qualify for CalEITC — ITIN filers also qualify",
                ))
        if "disabled" in special_circumstances or "pregnant" in special_circumstances:
            eligible.append(_build_result(
                "ca_sdi",
                "High",
                "60-70% of weekly wages; up to ~$1,620/week for up to 52 weeks",
                "California workers unable to work due to disability or pregnancy qualify for SDI",
            ))
        elif household_size >= 2:
            potentially_eligible.append(_build_result(
                "ca_sdi",
                "Medium",
                "8 weeks at 60-70% of wages for bonding with a new child",
                "California Paid Family Leave covers bonding with a new baby or caring for a family member",
            ))

    # -- New York-specific --
    if state_abbr == "NY" and employment_status in ("employed", "self_employed"):
        eitc_est = _estimate_eitc(annual_income, household_size)
        ny_est = int(eitc_est * 0.30)
        if ny_est > 0:
            eligible.append(_build_result(
                "ny_eitc",
                "High",
                f"~${ny_est:,} state credit (30% of federal EITC) + additional 5% for NYC residents",
                "New York State offers one of the most generous state EITCs at 30% of the federal credit",
            ))

    # -- Washington-specific --
    if state_abbr == "WA" and employment_status in ("employed", "self_employed"):
        eitc_est = _estimate_eitc(annual_income, household_size)
        if eitc_est > 0:
            children = max(0, min(household_size - 1, 3))
            wa_est = {0: 315, 1: 630, 2: 940, 3: 1255}.get(min(children, 3), 1255)
            eligible.append(_build_result(
                "wa_wftc",
                "High",
                f"${wa_est}/year Working Families Tax Credit",
                "Washington State's Working Families Tax Credit — ITIN filers also qualify",
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


def _get_state_abbr(state: str) -> str:
    """Convert a state name or abbreviation to a 2-letter abbreviation."""
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
    s = state.upper().strip()
    return name_to_abbr.get(s, s[:2] if len(s) > 2 else s)


def _estimate_caleitc(annual_income: float, household_size: int) -> int:
    """Estimate California CalEITC + Young Child Tax Credit (2023 tax year)."""
    children = max(0, min(household_size - 1, 3))
    # CalEITC max credits by number of children (2023)
    max_credits = {0: 255, 1: 1700, 2: 2816, 3: 3529}
    max_credit = max_credits.get(children, 3529)
    # Very rough phase-in/phase-out
    if annual_income < 8000:
        caleitc = int(max_credit * 0.7)
    elif annual_income < 20000:
        caleitc = max_credit
    elif annual_income < 28000:
        caleitc = int(max_credit * 0.6)
    else:
        caleitc = int(max_credit * 0.3)
    # Add Young Child Tax Credit ($1,117 per child under 6 — we can't know exact age, so estimate 1 young child)
    yctc = 1117 if children >= 1 else 0
    return caleitc + yctc


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
