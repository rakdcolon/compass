"""
Federal and state benefits programs knowledge base.
Eligibility thresholds reflect 2024 federal guidelines.
"""

from typing import Optional

BENEFITS_PROGRAMS = [
    {
        "id": "snap",
        "name": "SNAP (Supplemental Nutrition Assistance Program)",
        "short_name": "SNAP / Food Stamps",
        "category": "food",
        "description": (
            "SNAP provides monthly funds on an EBT card to buy groceries. "
            "It's the largest federal nutrition assistance program, serving 42 million Americans."
        ),
        "eligibility": {
            "gross_income_pct_fpl": 130,  # 130% FPL gross income limit
            "net_income_pct_fpl": 100,
            "asset_limit_dollars": 2750,  # $2,750 or $4,250 if elderly/disabled
            "citizenship": "citizens or qualified non-citizens",
            "age_requirement": None,
            "special_rules": [
                "Unemployed able-bodied adults (18-49) without dependents limited to 3 months unless working 20hrs/week",
                "Categorical eligibility in many states expands income/asset limits",
            ],
        },
        "avg_benefit": {
            "individual": "$197/month",
            "family_of_3": "$600/month",
            "max_family_of_4": "$973/month",
        },
        "apply_url": "https://www.benefits.gov/benefit/361",
        "how_to_apply": "Apply at your state SNAP office, online via your state benefits portal, or by calling 1-800-221-5689",
        "portal_steps": [
            "Go to benefits.gov and search for SNAP",
            "Click 'Apply Now' to be directed to your state portal",
            "Complete the online application with income and household information",
            "Submit verification documents (pay stubs, ID, utility bill)",
        ],
        "timeline": "Decision typically within 30 days; expedited 7-day processing if income < $150/month or rent > income",
        "tags": ["food", "nutrition", "groceries", "ebt", "low-income"],
    },
    {
        "id": "medicaid",
        "name": "Medicaid",
        "short_name": "Medicaid",
        "category": "healthcare",
        "description": (
            "Medicaid provides free or low-cost health coverage for low-income adults, children, "
            "pregnant women, elderly adults, and people with disabilities. Available in all 50 states."
        ),
        "eligibility": {
            "gross_income_pct_fpl": 138,  # ACA expansion states
            "net_income_pct_fpl": None,
            "asset_limit_dollars": None,  # No asset test in expansion states
            "citizenship": "citizens and certain qualified non-citizens; emergency Medicaid for others",
            "age_requirement": None,
            "special_rules": [
                "Income limit varies by state — expansion states cover up to 138% FPL for adults",
                "Non-expansion states may have lower income limits for adults without children",
                "Pregnant women often covered up to 200-375% FPL depending on state",
                "Children covered under CHIP at higher income levels",
            ],
        },
        "avg_benefit": {
            "individual": "Comprehensive coverage worth ~$8,000/year",
            "family": "Free preventive care, doctor visits, prescriptions, hospital stays",
        },
        "apply_url": "https://www.healthcare.gov/medicaid-chip/",
        "how_to_apply": "Apply at Healthcare.gov, your state Medicaid office, or call 1-877-267-2323",
        "portal_steps": [
            "Go to healthcare.gov",
            "Click 'See if you qualify for Medicaid'",
            "Enter your state and household information",
            "Complete the application and submit",
        ],
        "timeline": "Eligibility determined within 45 days (90 days for disability-based)",
        "tags": ["healthcare", "health insurance", "medical", "doctor", "hospital", "prescription"],
    },
    {
        "id": "chip",
        "name": "CHIP (Children's Health Insurance Program)",
        "short_name": "CHIP",
        "category": "healthcare",
        "description": (
            "CHIP provides low-cost health coverage to children in families that earn too much for Medicaid "
            "but can't afford private insurance. Coverage includes doctor visits, immunizations, prescriptions, dental, and vision."
        ),
        "eligibility": {
            "gross_income_pct_fpl": 200,  # varies by state, typically 200-300% FPL
            "net_income_pct_fpl": None,
            "asset_limit_dollars": None,
            "citizenship": "children who are citizens or qualifying immigrants",
            "age_requirement": "children under age 19",
            "special_rules": [
                "Many states cover children up to 300% FPL",
                "Some states also cover pregnant women under CHIP",
                "Low or no premiums depending on income",
            ],
        },
        "avg_benefit": {
            "child": "Comprehensive coverage for $0-$50/month depending on income",
        },
        "apply_url": "https://www.insurekidsnow.gov/",
        "how_to_apply": "Apply at InsureKidsNow.gov or call 1-877-543-7669",
        "portal_steps": [
            "Go to insurekidsnow.gov",
            "Enter your state",
            "Click 'Apply for CHIP'",
            "Complete the children's health coverage application",
        ],
        "timeline": "Decision typically within 45 days",
        "tags": ["children", "kids", "healthcare", "dental", "vision", "insurance"],
    },
    {
        "id": "tanf",
        "name": "TANF (Temporary Assistance for Needy Families)",
        "short_name": "TANF / Cash Assistance",
        "category": "cash_assistance",
        "description": (
            "TANF provides temporary cash assistance to low-income families with children. "
            "It can help cover basic needs like rent, utilities, and clothing while working toward self-sufficiency."
        ),
        "eligibility": {
            "gross_income_pct_fpl": 60,  # varies widely by state
            "net_income_pct_fpl": None,
            "asset_limit_dollars": 2000,  # varies by state
            "citizenship": "citizens; some qualified non-citizens after 5-year bar",
            "age_requirement": "Must have dependent child under 18 (or 19 if in school)",
            "special_rules": [
                "Lifetime limit of 60 months of federal TANF; states may have shorter limits",
                "Work requirements typically apply — must work or participate in work activities",
                "Benefit amounts vary significantly by state",
            ],
        },
        "avg_benefit": {
            "family_of_3": "$447/month (national average; varies from ~$150 to $900+)",
        },
        "apply_url": "https://www.benefits.gov/benefit/613",
        "how_to_apply": "Apply at your local TANF/welfare office or state benefits portal",
        "portal_steps": [
            "Search for your state's TANF application portal",
            "Create an account and complete the application",
            "Provide household, income, and employment information",
            "Attend required interview at local office",
        ],
        "timeline": "Usually approved within 45 days; emergency assistance sometimes available immediately",
        "tags": ["cash", "money", "family", "children", "rent", "utilities", "emergency"],
    },
    {
        "id": "wic",
        "name": "WIC (Women, Infants, and Children)",
        "short_name": "WIC",
        "category": "food",
        "description": (
            "WIC provides healthy foods, nutrition counseling, and referrals to health and social services "
            "for pregnant women, new mothers, infants, and children up to age 5."
        ),
        "eligibility": {
            "gross_income_pct_fpl": 185,
            "net_income_pct_fpl": None,
            "asset_limit_dollars": None,
            "citizenship": "no citizenship requirement — includes undocumented immigrants",
            "age_requirement": "Pregnant/postpartum/breastfeeding women; infants and children under 5",
            "special_rules": [
                "If already receiving SNAP, Medicaid, or TANF, automatically income-eligible",
                "Must have a nutritional need (most qualify)",
                "Available regardless of immigration status",
            ],
        },
        "avg_benefit": {
            "individual": "$50-$75/month in food vouchers plus nutrition support",
        },
        "apply_url": "https://www.fns.usda.gov/wic/applicant-participant",
        "how_to_apply": "Find your local WIC clinic at benefits.gov or call 1-800-942-3678",
        "portal_steps": [
            "Go to benefits.gov and search WIC",
            "Find your local WIC clinic",
            "Call to schedule an appointment",
            "Bring ID, proof of income, and proof of residency",
        ],
        "timeline": "Appointments usually available within a few days",
        "tags": ["pregnant", "baby", "infant", "breastfeeding", "food", "nutrition", "mother", "child"],
    },
    {
        "id": "liheap",
        "name": "LIHEAP (Low Income Home Energy Assistance Program)",
        "short_name": "LIHEAP / Energy Assistance",
        "category": "utilities",
        "description": (
            "LIHEAP helps low-income households pay their heating and cooling bills, "
            "preventing dangerous situations and utility shutoffs."
        ),
        "eligibility": {
            "gross_income_pct_fpl": 150,
            "net_income_pct_fpl": None,
            "asset_limit_dollars": None,
            "citizenship": "varies by state",
            "age_requirement": None,
            "special_rules": [
                "Priority given to households with elderly, disabled, or very young children",
                "Funding is limited — apply early in the season",
                "Can also help with weatherization and energy-efficient improvements",
            ],
        },
        "avg_benefit": {
            "household": "$400-$600 per year for heating; varies by region and fuel costs",
        },
        "apply_url": "https://www.benefits.gov/benefit/623",
        "how_to_apply": "Apply through your state energy assistance office or 2-1-1 helpline",
        "portal_steps": [
            "Call 2-1-1 to find your local LIHEAP office",
            "Contact your utility company for emergency assistance programs",
            "Apply online at your state's LIHEAP portal",
            "Provide proof of income and recent utility bills",
        ],
        "timeline": "Emergency assistance can be processed in 24-48 hours if facing shutoff",
        "tags": ["energy", "utilities", "electricity", "heating", "cooling", "electric bill", "gas bill"],
    },
    {
        "id": "ssi",
        "name": "SSI (Supplemental Security Income)",
        "short_name": "SSI",
        "category": "disability_income",
        "description": (
            "SSI provides monthly cash payments to people who are 65 or older, blind, or disabled, "
            "and have limited income and resources. It helps cover basic needs like food, clothing, and shelter."
        ),
        "eligibility": {
            "gross_income_pct_fpl": None,
            "net_income_pct_fpl": None,
            "asset_limit_dollars": 2000,  # $2,000 individual, $3,000 couple
            "citizenship": "citizens and certain non-citizens",
            "age_requirement": "65 or older, OR blind or disabled at any age",
            "special_rules": [
                "2024 maximum benefit: $943/month individual, $1,415/month couple",
                "Many states add a supplemental payment on top of federal SSI",
                "If approved, often automatically qualifies for Medicaid",
                "Must have limited income from work, Social Security, or other sources",
            ],
        },
        "avg_benefit": {
            "individual": "Up to $943/month (2024) — average is ~$697/month",
        },
        "apply_url": "https://www.ssa.gov/ssi/",
        "how_to_apply": "Apply online at ssa.gov, call 1-800-772-1213, or visit your local Social Security office",
        "portal_steps": [
            "Go to ssa.gov/ssi",
            "Click 'Apply for SSI'",
            "Complete the disability/elderly application online",
            "Gather medical records and financial documents",
            "Attend any required interviews with Social Security",
        ],
        "timeline": "Decision typically 3-6 months; can appeal if denied",
        "tags": ["disability", "elderly", "senior", "blind", "disabled", "social security", "monthly payment"],
    },
    {
        "id": "section8",
        "name": "Section 8 / Housing Choice Voucher Program",
        "short_name": "Section 8 Housing",
        "category": "housing",
        "description": (
            "Section 8 vouchers help very low-income families, elderly, and disabled individuals "
            "afford safe, decent housing in the private market. The voucher pays a portion of rent directly to landlords."
        ),
        "eligibility": {
            "gross_income_pct_fpl": None,
            "max_income_pct_ami": 50,  # 50% of Area Median Income
            "asset_limit_dollars": None,
            "citizenship": "at least one family member must be a citizen or eligible non-citizen",
            "age_requirement": None,
            "special_rules": [
                "Priority typically given to families at 30% AMI or below",
                "Waiting lists are often very long (months to years)",
                "Must pass criminal background check",
                "Responsible for finding a landlord who accepts vouchers",
            ],
        },
        "avg_benefit": {
            "household": "Pays the difference between 30% of income and local fair market rent",
        },
        "apply_url": "https://www.hud.gov/program_offices/public_indian_housing/programs/hcv",
        "how_to_apply": "Apply through your local Public Housing Authority (PHA); find at HUD.gov",
        "portal_steps": [
            "Go to hud.gov to find your local PHA",
            "Contact PHA about current waitlist status",
            "Submit application when waitlist opens",
            "Provide documentation of income, household members, and current housing",
        ],
        "timeline": "Waitlists often 1-3+ years; emergency priority for domestic violence victims, disabled, homeless",
        "tags": ["rent", "housing", "apartment", "landlord", "voucher", "homeless", "shelter", "eviction"],
    },
    {
        "id": "eitc",
        "name": "EITC (Earned Income Tax Credit)",
        "short_name": "Earned Income Tax Credit",
        "category": "tax_credit",
        "description": (
            "The EITC is a refundable tax credit for working people with low to moderate income. "
            "Unlike most tax credits, it can result in a refund even if you owe no taxes. "
            "23% of eligible families miss out on this benefit."
        ),
        "eligibility": {
            "gross_income_pct_fpl": None,
            "max_income_2024": {
                "no_children": 18591,
                "1_child": 49084,
                "2_children": 55768,
                "3_plus_children": 59899,
            },
            "asset_limit_dollars": None,
            "citizenship": "must have valid SSN; some non-citizens qualify",
            "age_requirement": "Must be 25-64 if no children; no age limit with qualifying children",
            "special_rules": [
                "Must have earned income (wages, self-employment)",
                "Investment income must be $11,600 or less",
                "Must file a tax return to claim — even if no taxes owed",
                "Free tax prep available via VITA program (call 1-800-906-9887)",
            ],
        },
        "avg_benefit": {
            "no_children": "Up to $632 (2024)",
            "1_child": "Up to $4,213 (2024)",
            "2_children": "Up to $6,960 (2024)",
            "3_plus_children": "Up to $7,830 (2024)",
        },
        "apply_url": "https://www.irs.gov/credits-deductions/individuals/earned-income-tax-credit",
        "how_to_apply": "Claim on your federal tax return (Form 1040, Schedule EIC). Free help at VITA sites.",
        "portal_steps": [
            "File your federal tax return (IRS Free File if income < $79,000)",
            "Complete Schedule EIC with information about qualifying children",
            "IRS will calculate and include credit in your refund",
            "Consider free VITA tax prep at 1-800-906-9887",
        ],
        "timeline": "Refund typically within 21 days of e-filing; EITC refunds held until mid-February by law",
        "tags": ["taxes", "tax refund", "working", "income", "money", "annual", "IRS"],
    },
    {
        "id": "medicare_savings",
        "name": "Medicare Savings Programs",
        "short_name": "Medicare Savings",
        "category": "healthcare",
        "description": (
            "Medicare Savings Programs help people with limited income pay their Medicare premiums, "
            "deductibles, and copays. Billions go unclaimed each year — 60% of eligible seniors never enroll."
        ),
        "eligibility": {
            "gross_income_pct_fpl": 135,  # varies by program level
            "asset_limit_dollars": 10590,  # individual (2024)
            "citizenship": "must be eligible for Medicare",
            "age_requirement": "65+ or disabled with Medicare",
            "special_rules": [
                "QMB: Full Medicare cost sharing eliminated (income ≤ 100% FPL)",
                "SLMB: Part B premium paid (income 100-120% FPL)",
                "QI: Part B premium paid (income 120-135% FPL) — must apply annually",
                "Often also automatically qualifies for Extra Help for prescription drugs",
            ],
        },
        "avg_benefit": {
            "individual": "$2,000-$5,000/year in saved premiums and cost-sharing",
        },
        "apply_url": "https://www.medicare.gov/basics/costs/help/medicare-savings-program",
        "how_to_apply": "Apply through your state Medicaid office or call 1-800-MEDICARE (1-800-633-4227)",
        "portal_steps": [
            "Go to medicare.gov",
            "Click 'Get help paying costs'",
            "Find your state's Medicare Savings Program",
            "Apply through your state Medicaid office",
        ],
        "timeline": "Decision typically within 45 days; may be retroactive",
        "tags": ["medicare", "elderly", "senior", "65+", "premium", "insurance", "prescription", "drug coverage"],
    },
]

# Build lookup dict by ID
BENEFITS_BY_ID = {p["id"]: p for p in BENEFITS_PROGRAMS}

# Category descriptions for UI
BENEFIT_CATEGORIES = {
    "food": {"label": "Food Assistance", "icon": "🥗", "color": "green"},
    "healthcare": {"label": "Healthcare", "icon": "🏥", "color": "blue"},
    "cash_assistance": {"label": "Cash Assistance", "icon": "💰", "color": "yellow"},
    "utilities": {"label": "Utilities", "icon": "💡", "color": "orange"},
    "disability_income": {"label": "Disability & Income", "icon": "♿", "color": "purple"},
    "housing": {"label": "Housing", "icon": "🏠", "color": "red"},
    "tax_credit": {"label": "Tax Credits", "icon": "📋", "color": "teal"},
}
