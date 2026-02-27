"""
Pure unit tests for backend/tools/eligibility.py.

No AWS credentials, no network calls, no mocking needed.
All functions under test are deterministic pure Python.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import FPL_2024, get_fpl
from backend.tools.eligibility import (
    _estimate_eitc,
    _estimate_snap_benefit,
    _is_medicaid_expansion_state,
    check_benefit_eligibility,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _program_ids(result: dict, key: str = "eligible_programs") -> list[str]:
    return [p["id"] for p in result[key]]


# ---------------------------------------------------------------------------
# FPL helpers
# ---------------------------------------------------------------------------

class TestGetFpl:
    def test_household_1(self):
        assert get_fpl(1) == 15_060

    def test_household_4(self):
        assert get_fpl(4) == 31_200

    def test_household_8(self):
        assert get_fpl(8) == 52_720

    def test_household_9_extrapolates(self):
        assert get_fpl(9) == get_fpl(8) + 5_380

    def test_household_12_extrapolates(self):
        assert get_fpl(12) == get_fpl(8) + 4 * 5_380


# ---------------------------------------------------------------------------
# Medicaid expansion state lookup
# ---------------------------------------------------------------------------

class TestMedicaidExpansionState:
    def test_california_expansion(self):
        assert _is_medicaid_expansion_state("CA") is True

    def test_california_full_name(self):
        assert _is_medicaid_expansion_state("California") is True

    def test_texas_non_expansion(self):
        assert _is_medicaid_expansion_state("TX") is False

    def test_florida_non_expansion(self):
        assert _is_medicaid_expansion_state("FL") is False

    def test_new_york_expansion(self):
        assert _is_medicaid_expansion_state("NY") is True

    def test_case_insensitive(self):
        assert _is_medicaid_expansion_state("ca") is True


# ---------------------------------------------------------------------------
# SNAP
# ---------------------------------------------------------------------------

class TestSnap:
    """130% FPL gross limit; 130–200% goes to potentially_eligible."""

    BASE = dict(
        household_size=4,
        state="CA",
        age=35,
        employment_status="unemployed",
        special_circumstances=[],
    )
    FPL4 = FPL_2024[4]  # 31_200

    def test_snap_at_130_pct_fpl_eligible(self):
        income = self.FPL4 * 1.30  # exactly 130%
        result = check_benefit_eligibility(annual_income=income, **self.BASE)
        assert "snap" in _program_ids(result)

    def test_snap_at_130_pct_fpl_likelihood_high(self):
        income = self.FPL4 * 1.30
        result = check_benefit_eligibility(annual_income=income, **self.BASE)
        snap = next(p for p in result["eligible_programs"] if p["id"] == "snap")
        assert snap["likelihood"] == "High"

    def test_snap_just_above_130_pct_fpl_potentially_eligible(self):
        # 131% puts it in the 130–200 "potentially eligible" bucket
        income = self.FPL4 * 1.31
        result = check_benefit_eligibility(annual_income=income, **self.BASE)
        assert "snap" not in _program_ids(result)
        assert "snap" in _program_ids(result, "potentially_eligible")

    def test_snap_at_200_pct_fpl_potentially_eligible(self):
        income = self.FPL4 * 2.00
        result = check_benefit_eligibility(annual_income=income, **self.BASE)
        assert "snap" in _program_ids(result, "potentially_eligible")

    def test_snap_above_200_pct_fpl_not_eligible(self):
        income = self.FPL4 * 2.01
        result = check_benefit_eligibility(annual_income=income, **self.BASE)
        assert "snap" not in _program_ids(result)
        assert "snap" not in _program_ids(result, "potentially_eligible")

    def test_snap_zero_income_eligible(self):
        result = check_benefit_eligibility(annual_income=0, **self.BASE)
        assert "snap" in _program_ids(result)


# ---------------------------------------------------------------------------
# Medicaid
# ---------------------------------------------------------------------------

class TestMedicaid:
    def test_expansion_state_at_138_pct_fpl_eligible(self):
        fpl1 = FPL_2024[1]
        income = fpl1 * 1.38
        result = check_benefit_eligibility(
            annual_income=income,
            household_size=1,
            state="CA",
            age=30,
            employment_status="unemployed",
            special_circumstances=[],
        )
        assert "medicaid" in _program_ids(result)

    def test_expansion_state_above_138_pct_not_eligible(self):
        fpl1 = FPL_2024[1]
        income = fpl1 * 1.39
        result = check_benefit_eligibility(
            annual_income=income,
            household_size=1,
            state="CA",
            age=30,
            employment_status="unemployed",
            special_circumstances=[],
        )
        assert "medicaid" not in _program_ids(result)

    def test_non_expansion_state_at_65_pct_fpl_eligible(self):
        fpl1 = FPL_2024[1]
        income = fpl1 * 0.65
        result = check_benefit_eligibility(
            annual_income=income,
            household_size=1,
            state="TX",
            age=30,
            employment_status="unemployed",
            special_circumstances=[],
        )
        assert "medicaid" in _program_ids(result)

    def test_non_expansion_state_at_66_pct_not_eligible(self):
        fpl1 = FPL_2024[1]
        income = fpl1 * 0.66
        result = check_benefit_eligibility(
            annual_income=income,
            household_size=1,
            state="TX",
            age=30,
            employment_status="unemployed",
            special_circumstances=[],
        )
        assert "medicaid" not in _program_ids(result)

    def test_pregnant_woman_higher_limit(self):
        fpl1 = FPL_2024[1]
        income = fpl1 * 2.0  # 200% — above expansion limit but pregnant
        result = check_benefit_eligibility(
            annual_income=income,
            household_size=1,
            state="TX",
            age=25,
            employment_status="employed",
            special_circumstances=["pregnant"],
        )
        assert "medicaid" in _program_ids(result)


# ---------------------------------------------------------------------------
# EITC
# ---------------------------------------------------------------------------

class TestEitc:
    def test_employed_with_children_eligible(self):
        result = check_benefit_eligibility(
            annual_income=25_000,
            household_size=3,
            state="CA",
            age=30,
            employment_status="employed",
            special_circumstances=[],
        )
        assert "eitc" in _program_ids(result)

    def test_unemployed_not_eligible(self):
        result = check_benefit_eligibility(
            annual_income=25_000,
            household_size=3,
            state="CA",
            age=30,
            employment_status="unemployed",
            special_circumstances=[],
        )
        assert "eitc" not in _program_ids(result)

    def test_self_employed_eligible(self):
        result = check_benefit_eligibility(
            annual_income=18_000,
            household_size=2,
            state="FL",
            age=35,
            employment_status="self_employed",
            special_circumstances=[],
        )
        assert "eitc" in _program_ids(result)

    def test_estimate_eitc_zero_children(self):
        credit = _estimate_eitc(15_000, 1)
        assert credit == 632  # max for 0 children at plateau

    def test_estimate_eitc_one_child_at_plateau(self):
        credit = _estimate_eitc(15_000, 2)  # 1 qualifying child
        assert credit == 4213

    def test_estimate_eitc_two_children(self):
        credit = _estimate_eitc(15_000, 3)  # 2 qualifying children
        assert credit == 6960

    def test_estimate_eitc_phases_down_at_high_income(self):
        low = _estimate_eitc(15_000, 2)
        high = _estimate_eitc(35_000, 2)
        assert high < low


# ---------------------------------------------------------------------------
# SSI
# ---------------------------------------------------------------------------

class TestSsi:
    def test_disabled_low_income_eligible(self):
        result = check_benefit_eligibility(
            annual_income=8_000,
            household_size=1,
            state="CA",
            age=45,
            employment_status="disabled",
            special_circumstances=["disabled"],
        )
        assert "ssi" in _program_ids(result)

    def test_disabled_medium_income_medium_likelihood(self):
        result = check_benefit_eligibility(
            annual_income=15_000,
            household_size=1,
            state="CA",
            age=45,
            employment_status="disabled",
            special_circumstances=["disabled"],
        )
        ssi = next((p for p in result["eligible_programs"] if p["id"] == "ssi"), None)
        assert ssi is not None
        assert ssi["likelihood"] == "Medium"

    def test_disabled_income_over_20k_not_eligible(self):
        result = check_benefit_eligibility(
            annual_income=21_000,
            household_size=1,
            state="CA",
            age=45,
            employment_status="disabled",
            special_circumstances=["disabled"],
        )
        assert "ssi" not in _program_ids(result)

    def test_elderly_65_low_income_eligible(self):
        result = check_benefit_eligibility(
            annual_income=9_000,
            household_size=1,
            state="FL",
            age=65,
            employment_status="retired",
            special_circumstances=["elderly"],
        )
        assert "ssi" in _program_ids(result)


# ---------------------------------------------------------------------------
# Medicare Savings Programs
# ---------------------------------------------------------------------------

class TestMedicareSavings:
    def test_eligible_at_65_low_income(self):
        fpl1 = FPL_2024[1]
        income = fpl1 * 1.0  # 100% FPL — well under 135%
        result = check_benefit_eligibility(
            annual_income=income,
            household_size=1,
            state="TX",
            age=65,
            employment_status="retired",
            special_circumstances=["elderly"],
        )
        assert "medicare_savings" in _program_ids(result)

    def test_not_eligible_above_135_pct_fpl(self):
        fpl1 = FPL_2024[1]
        income = fpl1 * 1.36  # 136% — above the 135% limit
        result = check_benefit_eligibility(
            annual_income=income,
            household_size=1,
            state="TX",
            age=65,
            employment_status="retired",
            special_circumstances=[],
        )
        assert "medicare_savings" not in _program_ids(result)

    def test_not_eligible_under_65(self):
        result = check_benefit_eligibility(
            annual_income=12_000,
            household_size=1,
            state="CA",
            age=64,
            employment_status="unemployed",
            special_circumstances=[],
        )
        assert "medicare_savings" not in _program_ids(result)


# ---------------------------------------------------------------------------
# Section 8
# ---------------------------------------------------------------------------

class TestSection8:
    def test_eligible_under_80_pct_fpl(self):
        fpl4 = FPL_2024[4]
        income = fpl4 * 0.80  # exactly 80% FPL
        result = check_benefit_eligibility(
            annual_income=income,
            household_size=4,
            state="CA",
            age=35,
            employment_status="employed",
            special_circumstances=[],
        )
        assert "section8" in _program_ids(result)

    def test_not_eligible_above_80_pct_fpl(self):
        fpl4 = FPL_2024[4]
        income = fpl4 * 0.81  # just above 80% FPL
        result = check_benefit_eligibility(
            annual_income=income,
            household_size=4,
            state="CA",
            age=35,
            employment_status="employed",
            special_circumstances=[],
        )
        assert "section8" not in _program_ids(result)

    def test_homeless_gets_high_priority(self):
        fpl1 = FPL_2024[1]
        income = fpl1 * 0.50
        result = check_benefit_eligibility(
            annual_income=income,
            household_size=1,
            state="CA",
            age=35,
            employment_status="unemployed",
            special_circumstances=["homeless"],
        )
        section8 = next(p for p in result["eligible_programs"] if p["id"] == "section8")
        assert section8["likelihood"] == "High"


# ---------------------------------------------------------------------------
# High-income household — no programs
# ---------------------------------------------------------------------------

class TestHighIncome:
    def test_no_programs_at_high_income(self):
        result = check_benefit_eligibility(
            annual_income=120_000,
            household_size=4,
            state="TX",
            age=40,
            employment_status="employed",
            special_circumstances=[],
        )
        assert result["eligible_programs"] == []
        assert result["potentially_eligible"] == []

    def test_summary_contains_income_pct(self):
        result = check_benefit_eligibility(
            annual_income=31_200,
            household_size=4,
            state="CA",
            age=35,
            employment_status="unemployed",
            special_circumstances=[],
        )
        assert "100%" in result["summary"] or "100" in result["summary"]


# ---------------------------------------------------------------------------
# Zero-income household of 4 — should qualify for many programs
# ---------------------------------------------------------------------------

class TestZeroIncome:
    def test_zero_income_qualifies_for_snap_and_medicaid(self):
        result = check_benefit_eligibility(
            annual_income=0,
            household_size=4,
            state="CA",
            age=35,
            employment_status="unemployed",
            special_circumstances=[],
        )
        ids = _program_ids(result)
        assert "snap" in ids
        assert "medicaid" in ids

    def test_zero_income_has_results_flag(self):
        result = check_benefit_eligibility(
            annual_income=0,
            household_size=4,
            state="CA",
            age=35,
            employment_status="unemployed",
            special_circumstances=[],
        )
        assert result["total_programs_found"] > 0


# ---------------------------------------------------------------------------
# TANF
# ---------------------------------------------------------------------------

class TestTanf:
    def test_family_with_children_very_low_income(self):
        fpl3 = FPL_2024[3]
        income = fpl3 * 0.50  # 50% FPL — well under 60%
        result = check_benefit_eligibility(
            annual_income=income,
            household_size=3,
            state="CA",
            age=28,
            employment_status="unemployed",
            special_circumstances=[],
        )
        assert "tanf" in _program_ids(result)

    def test_single_person_not_eligible(self):
        result = check_benefit_eligibility(
            annual_income=5_000,
            household_size=1,
            state="CA",
            age=28,
            employment_status="unemployed",
            special_circumstances=[],
        )
        # TANF requires household_size >= 2
        assert "tanf" not in _program_ids(result)
