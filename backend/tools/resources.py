"""
Local resource finder tool.
Returns nearby community resources based on needs and location.
Includes realistic demo data organized by region.
"""

from typing import Any


# Regional resource data (demo data representative of real resources)
RESOURCE_DATABASE = {
    "food": [
        {
            "name": "City Food Bank",
            "type": "food_bank",
            "services": ["groceries", "hot_meals", "produce"],
            "phone": "211",
            "website": "https://www.feedingamerica.org/find-your-local-foodbank",
            "hours": "Mon-Fri 9am-5pm, Sat 9am-1pm",
            "notes": "No ID required. Serves all zip codes in the metro area.",
        },
        {
            "name": "Community Kitchen & Pantry",
            "type": "pantry",
            "services": ["groceries", "baby_formula", "diapers"],
            "phone": "2-1-1",
            "website": "https://www.feedingamerica.org",
            "hours": "Tue, Thu 10am-3pm",
            "notes": "Brings food directly to families with young children.",
        },
        {
            "name": "SNAP Enrollment Assistance",
            "type": "benefits_navigator",
            "services": ["snap_enrollment", "benefits_screening"],
            "phone": "1-800-221-5689",
            "website": "https://www.benefits.gov/benefit/361",
            "hours": "Mon-Fri 8am-6pm",
            "notes": "Free help applying for food stamps in your language.",
        },
    ],
    "healthcare": [
        {
            "name": "Community Health Center",
            "type": "clinic",
            "services": ["primary_care", "dental", "mental_health", "prenatal"],
            "phone": "1-877-464-4772",
            "website": "https://findahealthcenter.hrsa.gov/",
            "hours": "Mon-Fri 8am-6pm, some evening/weekend hours",
            "notes": "Federally Qualified Health Center — charges on sliding scale based on income. Nobody turned away.",
        },
        {
            "name": "Free & Charitable Clinics",
            "type": "free_clinic",
            "services": ["primary_care", "prescriptions", "lab_work"],
            "phone": "1-800-955-5765",
            "website": "https://www.nafcclinics.org/find-clinic",
            "hours": "Varies by location",
            "notes": "Over 1,400 free clinics nationwide. Income eligibility applies.",
        },
        {
            "name": "Medicaid Enrollment Help",
            "type": "benefits_navigator",
            "services": ["medicaid_enrollment", "chip_enrollment", "marketplace"],
            "phone": "1-877-267-2323",
            "website": "https://www.healthcare.gov/find-assistance/",
            "hours": "24/7 helpline",
            "notes": "Free navigators can help you enroll in Medicaid or marketplace plans.",
        },
        {
            "name": "Patient Advocate Foundation",
            "type": "advocacy",
            "services": ["insurance_appeals", "medication_assistance", "case_management"],
            "phone": "1-800-532-5274",
            "website": "https://www.patientadvocate.org",
            "hours": "Mon-Fri 8:30am-5:30pm ET",
            "notes": "Free case management for chronic/life-threatening conditions.",
        },
    ],
    "housing": [
        {
            "name": "Local Housing Authority",
            "type": "public_housing",
            "services": ["section8_applications", "public_housing", "waitlist"],
            "phone": "1-800-569-4287",
            "website": "https://www.hud.gov/program_offices/public_indian_housing",
            "hours": "Mon-Fri 9am-5pm",
            "notes": "Apply for Section 8 housing vouchers and public housing.",
        },
        {
            "name": "Emergency Shelter Network",
            "type": "shelter",
            "services": ["emergency_shelter", "transitional_housing", "meals"],
            "phone": "2-1-1",
            "website": "https://www.211.org",
            "hours": "24/7",
            "notes": "Call 2-1-1 anytime for immediate shelter referrals.",
        },
        {
            "name": "Legal Aid Housing Help",
            "type": "legal_aid",
            "services": ["eviction_defense", "tenant_rights", "security_deposit"],
            "phone": "1-800-342-5297",
            "website": "https://www.lawhelp.org",
            "hours": "Mon-Fri 9am-5pm",
            "notes": "Free legal help if facing eviction or housing discrimination.",
        },
        {
            "name": "Rental Assistance Program",
            "type": "financial_assistance",
            "services": ["rent_assistance", "security_deposit", "utility_deposit"],
            "phone": "2-1-1",
            "website": "https://www.consumerfinance.gov/renthelp/",
            "hours": "Mon-Fri 9am-5pm",
            "notes": "Emergency rental assistance may be available through local programs.",
        },
    ],
    "utilities": [
        {
            "name": "LIHEAP Energy Assistance",
            "type": "energy_assistance",
            "services": ["heating_bill", "cooling_bill", "crisis_assistance"],
            "phone": "2-1-1",
            "website": "https://www.acf.hhs.gov/ocs/map/liheap-map-state-and-territory-contact-listing",
            "hours": "Mon-Fri 8am-5pm",
            "notes": "Apply early — funds run out. Priority for elderly and disabled.",
        },
        {
            "name": "Utility Company Assistance",
            "type": "utility_program",
            "services": ["bill_reduction", "payment_plans", "shutoff_prevention"],
            "phone": "On your utility bill",
            "website": "https://www.benefits.gov/benefit/623",
            "hours": "Business hours",
            "notes": "Call your utility company directly about income-based programs and payment plans.",
        },
    ],
    "mental_health": [
        {
            "name": "Crisis Text Line",
            "type": "crisis_support",
            "services": ["crisis_counseling", "mental_health_support"],
            "phone": "Text HOME to 741741",
            "website": "https://www.crisistextline.org",
            "hours": "24/7",
            "notes": "Free, confidential crisis support via text. Any crisis, any time.",
        },
        {
            "name": "SAMHSA National Helpline",
            "type": "mental_health",
            "services": ["mental_health", "substance_use", "referrals"],
            "phone": "1-800-662-4357",
            "website": "https://www.samhsa.gov/find-help/national-helpline",
            "hours": "24/7, 365 days",
            "notes": "Free, confidential treatment referral. Available in English and Spanish.",
        },
        {
            "name": "Open Path Collective",
            "type": "counseling",
            "services": ["therapy", "counseling", "sliding_scale"],
            "phone": "N/A",
            "website": "https://openpathcollective.org",
            "hours": "Schedule online",
            "notes": "Affordable therapy sessions ($30-$80) from licensed therapists.",
        },
    ],
    "legal": [
        {
            "name": "Legal Aid Society",
            "type": "legal_aid",
            "services": ["immigration", "family_law", "housing", "benefits_appeals"],
            "phone": "1-800-342-5297",
            "website": "https://www.lawhelp.org",
            "hours": "Mon-Fri 9am-5pm",
            "notes": "Free civil legal services for low-income individuals and families.",
        },
        {
            "name": "Immigration Legal Help",
            "type": "immigration",
            "services": ["visa_help", "asylum", "citizenship", "DACA"],
            "phone": "1-800-375-5283",
            "website": "https://www.immigrationadvocates.org",
            "hours": "Mon-Fri 9am-5pm",
            "notes": "Find BIA-accredited immigration legal help near you.",
        },
    ],
    "employment": [
        {
            "name": "American Job Centers",
            "type": "employment",
            "services": ["job_search", "resume_help", "training", "unemployment"],
            "phone": "1-877-872-5627",
            "website": "https://www.careeronestop.org",
            "hours": "Mon-Fri 8am-5pm",
            "notes": "Free job search help, resume workshops, skills training. 2,500 locations.",
        },
        {
            "name": "Unemployment Insurance",
            "type": "benefits",
            "services": ["unemployment_claims", "job_search_assistance"],
            "phone": "Your state UI office",
            "website": "https://www.careeronestop.org/LocalHelp/UnemploymentBenefits/find-unemployment-benefits.aspx",
            "hours": "Mon-Fri business hours",
            "notes": "Apply for unemployment benefits through your state if recently laid off.",
        },
    ],
    "childcare": [
        {
            "name": "Child Care Subsidy Program (CCAP)",
            "type": "childcare",
            "services": ["childcare_assistance", "after_school", "preschool"],
            "phone": "1-800-424-2246",
            "website": "https://www.benefits.gov/categories/Childcare",
            "hours": "Mon-Fri 9am-5pm",
            "notes": "Subsidized childcare for low-income working families.",
        },
        {
            "name": "Head Start / Early Head Start",
            "type": "education",
            "services": ["free_preschool", "childcare", "family_support"],
            "phone": "1-866-763-6481",
            "website": "https://www.acf.hhs.gov/ohs",
            "hours": "School hours",
            "notes": "Free comprehensive early childhood programs for children 0-5.",
        },
    ],
}

# Needs vocabulary mapping (user terms → database categories)
NEEDS_MAPPING = {
    # Food
    "food": "food", "groceries": "food", "hungry": "food", "starving": "food",
    "eating": "food", "meals": "food", "snap": "food", "ebt": "food",
    # Healthcare
    "healthcare": "healthcare", "doctor": "healthcare", "medical": "healthcare",
    "hospital": "healthcare", "sick": "healthcare", "medicine": "healthcare",
    "prescription": "healthcare", "dental": "healthcare", "health": "healthcare",
    "insurance": "healthcare", "medicaid": "healthcare",
    # Housing
    "housing": "housing", "rent": "housing", "homeless": "housing", "shelter": "housing",
    "eviction": "housing", "apartment": "housing", "home": "housing",
    # Utilities
    "electricity": "utilities", "electric": "utilities", "gas": "utilities",
    "utilities": "utilities", "heat": "utilities", "cooling": "utilities",
    "energy": "utilities", "bill": "utilities",
    # Mental health
    "mental": "mental_health", "depression": "mental_health", "anxiety": "mental_health",
    "counseling": "mental_health", "therapy": "mental_health", "crisis": "mental_health",
    "substance": "mental_health", "addiction": "mental_health",
    # Legal
    "legal": "legal", "lawyer": "legal", "immigration": "legal", "deportation": "legal",
    "visa": "legal", "asylum": "legal", "citizenship": "legal",
    # Employment
    "job": "employment", "work": "employment", "employment": "employment",
    "unemployed": "employment", "fired": "employment", "laid off": "employment",
    "resume": "employment", "training": "employment",
    # Childcare
    "childcare": "childcare", "daycare": "childcare", "preschool": "childcare",
    "babysitter": "childcare", "kids": "childcare", "children": "childcare",
}


def find_local_resources(
    zip_code: str,
    needs_list: list[str],
    language: str = "en",
) -> dict[str, Any]:
    """
    Find local community resources based on needs.

    Args:
        zip_code: User's zip code or city/state
        needs_list: List of needs (e.g., ['food', 'healthcare', 'rent'])
        language: Preferred language code ('en', 'es', 'fr', etc.)

    Returns:
        dict with 'resources' list and 'hotlines' for immediate help
    """
    # Resolve needs to categories
    categories = set()
    for need in needs_list:
        need_lower = need.lower().strip()
        # Direct match
        if need_lower in RESOURCE_DATABASE:
            categories.add(need_lower)
        else:
            # Fuzzy match via mapping
            for keyword, category in NEEDS_MAPPING.items():
                if keyword in need_lower or need_lower in keyword:
                    categories.add(category)

    # Always include food and healthcare as baseline
    if not categories:
        categories = {"food", "healthcare"}

    # Gather resources from matched categories
    resources = []
    seen_names = set()
    for category in sorted(categories):
        for resource in RESOURCE_DATABASE.get(category, []):
            if resource["name"] not in seen_names:
                resource_with_meta = {**resource, "category": category}
                # Add language note if non-English
                if language != "en" and language in ("es", "spanish"):
                    resource_with_meta["language_note"] = "Spanish-speaking staff available at most locations"
                resources.append(resource_with_meta)
                seen_names.add(resource["name"])

    # Universal hotlines always included
    hotlines = [
        {
            "name": "2-1-1 Helpline",
            "description": "Free, confidential referrals for food, housing, healthcare, crisis services",
            "contact": "Call or text 2-1-1",
            "available": "24/7",
            "languages": "200+ languages",
        },
        {
            "name": "Benefits.gov",
            "description": "Find all federal benefit programs you may qualify for",
            "contact": "https://www.benefits.gov",
            "available": "24/7 online",
            "languages": "English and Spanish",
        },
    ]

    if "mental_health" in categories or "crisis" in str(needs_list).lower():
        hotlines.append({
            "name": "988 Suicide & Crisis Lifeline",
            "description": "Free, confidential mental health crisis support",
            "contact": "Call or text 9-8-8",
            "available": "24/7",
            "languages": "English, Spanish, and more",
        })

    location_display = zip_code if zip_code else "your area"

    return {
        "location": location_display,
        "resources": resources,
        "hotlines": hotlines,
        "total_resources": len(resources),
        "categories_found": list(categories),
        "summary": (
            f"Found {len(resources)} resources near {location_display} "
            f"covering {', '.join(categories)}. "
            f"You can also call 2-1-1 anytime for immediate local referrals."
        ),
    }
