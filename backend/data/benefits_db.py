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
    # -----------------------------------------------------------------------
    # Additional federal programs
    # -----------------------------------------------------------------------
    {
        "id": "ssdi",
        "name": "SSDI (Social Security Disability Insurance)",
        "short_name": "SSDI",
        "category": "disability_income",
        "description": (
            "SSDI pays monthly benefits to workers who become disabled before retirement age "
            "and can no longer work. Unlike SSI, SSDI is based on your work history and Social Security taxes paid."
        ),
        "eligibility": {
            "gross_income_pct_fpl": None,
            "asset_limit_dollars": None,
            "citizenship": "citizens and certain non-citizens with work history",
            "age_requirement": "Under full retirement age; must have sufficient work credits",
            "special_rules": [
                "Must have a medically determinable impairment lasting 12+ months or expected to result in death",
                "Substantial Gainful Activity (SGA) limit: $1,550/month in 2024 ($2,590 for blind)",
                "5-month waiting period before benefits begin",
                "After 24 months of SSDI, automatically enrolled in Medicare",
            ],
        },
        "avg_benefit": {
            "individual": "~$1,537/month average (2024); depends on work history",
        },
        "apply_url": "https://www.ssa.gov/disability/",
        "how_to_apply": "Apply online at ssa.gov/disability, call 1-800-772-1213, or visit a local Social Security office",
        "portal_steps": [
            "Go to ssa.gov/disability",
            "Click 'Apply for Disability Benefits'",
            "Gather medical records, work history, and doctor information",
            "Complete and submit the online application",
            "Follow up with any requested documentation",
        ],
        "timeline": "Initial decision typically 3-6 months; appeals can add 1-2 years",
        "tags": ["disability", "disabled", "worker", "social security", "SSDI", "monthly payment", "cannot work"],
    },
    {
        "id": "unemployment_insurance",
        "name": "Unemployment Insurance (UI)",
        "short_name": "Unemployment Benefits",
        "category": "cash_assistance",
        "description": (
            "Unemployment Insurance provides temporary weekly cash payments to workers who lose their jobs "
            "through no fault of their own. Administered by each state, with benefit amounts and duration varying widely."
        ),
        "eligibility": {
            "gross_income_pct_fpl": None,
            "asset_limit_dollars": None,
            "citizenship": "varies by state; generally requires work authorization",
            "age_requirement": None,
            "special_rules": [
                "Must have lost job through no fault of your own (layoff, reduction in force)",
                "Must meet your state's minimum wage/hours worked requirements",
                "Must be actively seeking new work and able to work",
                "Self-employed and gig workers generally not eligible (except during federal expansions)",
            ],
        },
        "avg_benefit": {
            "individual": "~40-50% of prior wages; average ~$440/week nationally; up to 26 weeks",
        },
        "apply_url": "https://www.careeronestop.org/LocalHelp/UnemploymentBenefits/find-unemployment-benefits.aspx",
        "how_to_apply": "Apply through your state's unemployment office website immediately after job loss",
        "portal_steps": [
            "Go to your state's unemployment insurance website",
            "Create an account and file an initial claim",
            "Provide your employment history and reason for separation",
            "Certify weekly or bi-weekly to continue receiving benefits",
        ],
        "timeline": "First payment typically within 2-3 weeks of filing; file immediately after job loss",
        "tags": ["unemployment", "job loss", "laid off", "weekly payment", "work", "income replacement"],
    },
    {
        "id": "extra_help",
        "name": "Extra Help (Medicare Part D Low Income Subsidy)",
        "short_name": "Extra Help / LIS",
        "category": "healthcare",
        "description": (
            "Extra Help (also called Low Income Subsidy) helps people with Medicare pay for prescription drug "
            "costs including premiums, deductibles, and copays. Worth up to $5,900/year in savings."
        ),
        "eligibility": {
            "gross_income_pct_fpl": 150,
            "asset_limit_dollars": 17220,  # individual (2024, excludes home/car)
            "citizenship": "must be enrolled in Medicare Part A or B",
            "age_requirement": "65+ or disabled with Medicare",
            "special_rules": [
                "Automatically eligible if you have Medicaid, SSI, or a Medicare Savings Program",
                "2024 income limit: ~$22,590 individual / ~$30,660 couple",
                "Asset limit: $17,220 individual / $34,360 couple (2024)",
                "Copays as low as $0-$11 for covered drugs",
            ],
        },
        "avg_benefit": {
            "individual": "Up to $5,900/year in prescription cost savings",
        },
        "apply_url": "https://www.ssa.gov/medicare/part-d/extra-help",
        "how_to_apply": "Apply at ssa.gov, call SSA at 1-800-772-1213, or apply through your state Medicaid office",
        "portal_steps": [
            "Go to ssa.gov/medicare/part-d/extra-help",
            "Complete the LIS application online",
            "Or call SSA at 1-800-772-1213 to apply by phone",
            "Approval is retroactive to application date",
        ],
        "timeline": "Decision typically within 2-3 weeks",
        "tags": ["medicare", "prescription", "drug costs", "elderly", "senior", "Part D", "LIS"],
    },
    {
        "id": "nslp",
        "name": "National School Lunch Program (NSLP)",
        "short_name": "Free/Reduced School Lunch",
        "category": "food",
        "description": (
            "The National School Lunch Program provides free or reduced-price nutritious lunches "
            "to children in participating schools. Free meals: ≤130% FPL. Reduced price ($0.40): ≤185% FPL."
        ),
        "eligibility": {
            "gross_income_pct_fpl": 185,  # reduced price; free is 130%
            "asset_limit_dollars": None,
            "citizenship": "no citizenship requirement",
            "age_requirement": "School-age children (K-12)",
            "special_rules": [
                "Free meals for families at or below 130% FPL",
                "Reduced-price meals ($0.40/lunch) for 130-185% FPL",
                "Directly certified for free meals if household receives SNAP or TANF",
                "Community Eligibility Provision: entire schools qualify in high-poverty areas",
            ],
        },
        "avg_benefit": {
            "child": "Free lunch worth ~$3.50/day; up to $630/school year per child",
        },
        "apply_url": "https://www.fns.usda.gov/nslp",
        "how_to_apply": "Apply through your child's school at the start of each school year",
        "portal_steps": [
            "Contact your child's school or district office",
            "Request and complete the free/reduced meal application",
            "Or apply online at your school district's website",
            "Approval is typically same day or within a week",
        ],
        "timeline": "Usually approved within a few days; benefits start immediately upon approval",
        "tags": ["school", "children", "kids", "lunch", "food", "education", "K-12"],
    },
    {
        "id": "ccdf",
        "name": "CCDF (Child Care and Development Fund)",
        "short_name": "Child Care Subsidy",
        "category": "childcare",
        "description": (
            "The Child Care and Development Fund helps low-income families pay for child care "
            "so parents can work, attend school, or participate in job training. Subsidies go directly to providers."
        ),
        "eligibility": {
            "gross_income_pct_fpl": 85,  # states set limits up to 85% SMI (~200% FPL equivalent)
            "asset_limit_dollars": None,
            "citizenship": "child must be citizen or qualifying non-citizen",
            "age_requirement": "Children under age 13 (up to 19 if disabled)",
            "special_rules": [
                "Parent must be working, in school, or in job training",
                "Income limits vary by state — up to 85% of state median income",
                "Families pay a co-pay based on income; subsidy covers the rest",
                "Waiting lists are common due to limited funding",
            ],
        },
        "avg_benefit": {
            "family": "Covers majority of child care costs; average $400-$1,200/month in subsidy value",
        },
        "apply_url": "https://www.childcare.gov/consumer-education/get-help-paying-for-child-care",
        "how_to_apply": "Apply through your state child care agency or benefits portal",
        "portal_steps": [
            "Go to childcare.gov to find your state's agency",
            "Contact your local child care resource and referral agency",
            "Complete the child care subsidy application",
            "Select an approved child care provider",
        ],
        "timeline": "Varies by state; waitlists common — apply as early as possible",
        "tags": ["child care", "daycare", "preschool", "working parent", "childcare", "subsidy"],
    },
    {
        "id": "lifeline",
        "name": "Lifeline Phone & Internet Subsidy",
        "short_name": "Lifeline",
        "category": "utilities",
        "description": (
            "Lifeline provides a monthly discount on phone or internet service for eligible low-income households. "
            "The ACP (Affordable Connectivity Program) extension may also provide additional broadband discounts."
        ),
        "eligibility": {
            "gross_income_pct_fpl": 135,
            "asset_limit_dollars": None,
            "citizenship": "must live in the US",
            "age_requirement": None,
            "special_rules": [
                "Automatically eligible if receiving SNAP, Medicaid, SSI, FPHA housing assistance, or Lifeline Tribal",
                "$9.25/month discount on phone or internet service ($34.25 on qualifying Tribal lands)",
                "One benefit per household",
                "Must use the service to maintain eligibility",
            ],
        },
        "avg_benefit": {
            "household": "$9.25/month discount (~$111/year); up to $34.25/month on Tribal lands",
        },
        "apply_url": "https://www.lifelinesupport.org/",
        "how_to_apply": "Apply at lifelinesupport.org or through participating phone/internet providers",
        "portal_steps": [
            "Go to lifelinesupport.org",
            "Check eligibility and apply online",
            "Or contact a participating provider (Verizon, AT&T, T-Mobile, etc.)",
            "Provide proof of eligibility (program enrollment or income)",
        ],
        "timeline": "Approval typically within a few days",
        "tags": ["phone", "internet", "broadband", "communication", "utilities", "technology"],
    },
    {
        "id": "head_start",
        "name": "Head Start & Early Head Start",
        "short_name": "Head Start",
        "category": "childcare",
        "description": (
            "Head Start provides free comprehensive early childhood education, health, nutrition, and parent "
            "involvement services to children from birth to age 5 in low-income families."
        ),
        "eligibility": {
            "gross_income_pct_fpl": 100,
            "asset_limit_dollars": None,
            "citizenship": "no citizenship requirement",
            "age_requirement": "Children from birth to age 5; Early Head Start: birth to 3",
            "special_rules": [
                "Priority for families at or below 100% FPL",
                "Children in foster care, experiencing homelessness, or with IEPs automatically eligible",
                "Some slots available for families up to 130% FPL",
                "Provides free preschool, meals, health screenings, and family support",
            ],
        },
        "avg_benefit": {
            "child": "Full-day preschool worth $10,000-$20,000/year per child",
        },
        "apply_url": "https://eclkc.ohs.acf.hhs.gov/center-locator",
        "how_to_apply": "Find your local Head Start program at the ACF Center Locator",
        "portal_steps": [
            "Go to eclkc.ohs.acf.hhs.gov/center-locator",
            "Enter your zip code to find local Head Start programs",
            "Contact the program directly to apply",
            "Provide income documentation and child's birth certificate",
        ],
        "timeline": "Enrollment typically opens in spring for the following school year; waitlists are common",
        "tags": ["preschool", "early childhood", "children", "education", "childcare", "infant", "toddler"],
    },
    {
        "id": "weatherization",
        "name": "Weatherization Assistance Program (WAP)",
        "short_name": "Weatherization",
        "category": "utilities",
        "description": (
            "The Weatherization Assistance Program provides free home energy efficiency improvements "
            "to low-income households — insulation, air sealing, HVAC repairs — reducing energy bills by an average of $283/year."
        ),
        "eligibility": {
            "gross_income_pct_fpl": 200,
            "asset_limit_dollars": None,
            "citizenship": "varies by state",
            "age_requirement": None,
            "special_rules": [
                "Priority for households with elderly members (60+), disabled, or children under 6",
                "Renters may qualify if landlord agrees to participate",
                "No repayment required — it's a grant",
                "Average energy savings of $283/year after weatherization",
            ],
        },
        "avg_benefit": {
            "household": "Free home improvements worth $5,000-$6,500; ~$283/year in energy savings",
        },
        "apply_url": "https://www.energy.gov/scep/wap/weatherization-assistance-program",
        "how_to_apply": "Apply through your local WAP agency or call 2-1-1",
        "portal_steps": [
            "Call 2-1-1 to find your local weatherization agency",
            "Or go to energy.gov/scep/wap and find your state contact",
            "Schedule a home energy audit",
            "Approved work is performed at no cost to you",
        ],
        "timeline": "Waitlists are common; service takes 1-2 days when scheduled",
        "tags": ["home", "energy", "insulation", "heating", "cooling", "utility bills", "home improvement"],
    },
    # -----------------------------------------------------------------------
    # Veterans programs
    # -----------------------------------------------------------------------
    {
        "id": "va_disability",
        "name": "VA Disability Compensation",
        "short_name": "VA Disability",
        "category": "disability_income",
        "description": (
            "VA Disability Compensation is a tax-free monthly payment for veterans with disabilities "
            "that were caused or worsened by military service. Amount depends on disability rating (10%-100%)."
        ),
        "eligibility": {
            "gross_income_pct_fpl": None,
            "asset_limit_dollars": None,
            "citizenship": "must be a veteran (discharged under conditions other than dishonorable)",
            "age_requirement": None,
            "special_rules": [
                "Disability must be service-connected (occurred or worsened during service)",
                "Ratings from 10% to 100%; higher rating = higher payment",
                "2024 rates: 10% = $171/month; 100% = $3,831+/month",
                "Tax-free benefit; does not affect SSI/SNAP eligibility thresholds",
                "Survivors may qualify for Dependency and Indemnity Compensation (DIC)",
            ],
        },
        "avg_benefit": {
            "veteran": "Ranges from $171/month (10%) to $3,831+/month (100%); average ~$1,400/month",
        },
        "apply_url": "https://www.va.gov/disability/",
        "how_to_apply": "Apply online at va.gov, call 1-800-827-1000, or visit a VA regional office",
        "portal_steps": [
            "Go to va.gov/disability/apply-for-disability-compensation-form-21-526ez",
            "Sign in with Login.gov or ID.me",
            "Complete VA Form 21-526EZ",
            "Gather service records, medical evidence, and buddy statements",
            "Submit and attend any scheduled C&P exams",
        ],
        "timeline": "Initial decisions in 100-125 days on average; appeals can take 1-3+ years",
        "tags": ["veteran", "military", "disability", "service-connected", "VA", "tax-free", "monthly payment"],
    },
    {
        "id": "va_pension",
        "name": "VA Pension (Non-Service-Connected)",
        "short_name": "VA Pension",
        "category": "cash_assistance",
        "description": (
            "VA Pension is a needs-based benefit for wartime veterans with limited income and net worth. "
            "Unlike VA Disability, it does not require a service-connected injury. Aid & Attendance adds extra for those needing care."
        ),
        "eligibility": {
            "gross_income_pct_fpl": None,
            "asset_limit_dollars": 155356,  # net worth limit 2024 (includes assets + income)
            "citizenship": "must be a wartime veteran (discharged honorably)",
            "age_requirement": "65+ OR totally and permanently disabled",
            "special_rules": [
                "Must have served at least 90 days active duty with at least 1 day during a wartime period",
                "Income limit: $16,551/year (single veteran, 2024) — reduced by unreimbursed medical expenses",
                "Net worth limit: $155,356 (2024)",
                "Aid & Attendance adds $1,881/month if needing help with daily activities",
                "Housebound benefit adds $407/month if substantially confined to home",
            ],
        },
        "avg_benefit": {
            "veteran": "Up to $1,254/month (single veteran, 2024); up to $3,261/month with Aid & Attendance",
        },
        "apply_url": "https://www.va.gov/pension/",
        "how_to_apply": "Apply at va.gov, call 1-800-827-1000, or use a VSO (Veterans Service Organization) for free help",
        "portal_steps": [
            "Go to va.gov/pension",
            "Complete VA Form 21P-527EZ",
            "Gather discharge papers (DD-214), medical records, and financial records",
            "Consider applying through a VSO (American Legion, VFW, DAV) for free assistance",
        ],
        "timeline": "Decisions typically take 4-12 months; Aid & Attendance can be processed faster",
        "tags": ["veteran", "military", "pension", "elderly", "senior", "wartime", "Aid and Attendance", "income"],
    },
    # -----------------------------------------------------------------------
    # Emergency / housing
    # -----------------------------------------------------------------------
    {
        "id": "emergency_rental",
        "name": "Emergency Rental Assistance (ERA)",
        "short_name": "Emergency Rental Assistance",
        "category": "housing",
        "description": (
            "ERA programs provide short-term help paying rent and utility arrears for households "
            "experiencing financial hardship. Funded federally but administered by states and localities — "
            "availability varies by location."
        ),
        "eligibility": {
            "gross_income_pct_fpl": None,
            "max_income_pct_ami": 80,  # 80% AMI
            "asset_limit_dollars": None,
            "citizenship": "varies by local program",
            "age_requirement": None,
            "special_rules": [
                "Must have experienced financial hardship (job loss, medical emergency, etc.)",
                "Must be at risk of housing instability or homelessness",
                "Income at or below 80% AMI",
                "Availability and amounts vary by state/county — call 2-1-1",
                "Can cover past-due rent, future rent, and utility arrears",
            ],
        },
        "avg_benefit": {
            "household": "Up to 12-18 months of rent/utility assistance; amounts vary by locality",
        },
        "apply_url": "https://www.consumerfinance.gov/coronavirus/mortgage-and-housing-assistance/renter-protections/find-help-with-rent-and-utilities/",
        "how_to_apply": "Call 2-1-1 or visit your local housing authority; programs vary by location",
        "portal_steps": [
            "Call 2-1-1 to find local ERA programs",
            "Contact your local housing authority or community action agency",
            "Gather documentation: lease, proof of hardship, income documentation",
            "Apply online or in person at the administering agency",
        ],
        "timeline": "Processing times vary widely — from days to weeks depending on program demand",
        "tags": ["rent", "housing", "eviction", "utilities", "emergency", "arrears", "behind on rent"],
    },
    # -----------------------------------------------------------------------
    # State-level programs (multi-state)
    # -----------------------------------------------------------------------
    {
        "id": "state_eitc",
        "name": "State Earned Income Tax Credit",
        "short_name": "State EITC",
        "category": "tax_credit",
        "description": (
            "31 states plus DC and Puerto Rico offer their own Earned Income Tax Credits on top of the federal EITC. "
            "State EITCs are typically 5-40% of the federal EITC — claiming both can significantly increase your refund."
        ),
        "eligibility": {
            "gross_income_pct_fpl": None,
            "asset_limit_dollars": None,
            "citizenship": "must qualify for federal EITC",
            "age_requirement": "Same as federal EITC",
            "special_rules": [
                "Must qualify for the federal EITC first",
                "Available in: CA, CO, CT, DC, DE, HI, IA, IL, IN, KS, LA, MA, MD, ME, MI, MN, MO, MT, NE, NJ, NM, NY, OH, OK, OR, RI, SC, TX, VA, VT, WA, WI",
                "Ranges from 5% (IA) to 40% (CA for CalEITC-equivalent) of federal credit",
                "Claim on your state income tax return",
            ],
        },
        "avg_benefit": {
            "individual": "Additional $100-$1,500+ depending on state and federal EITC amount",
        },
        "apply_url": "https://www.eitc.irs.gov/other-refundable-credits-toolkit/state-and-local-eitc/state-and-local-eitc",
        "how_to_apply": "Claim on your state income tax return; automatically calculated in most tax software",
        "portal_steps": [
            "File your federal tax return and claim the EITC",
            "File your state income tax return",
            "The state EITC is typically calculated automatically based on your federal EITC",
            "Use IRS Free File or VITA for free tax preparation",
        ],
        "timeline": "Received with state tax refund, typically within 2-4 weeks of e-filing",
        "tags": ["taxes", "tax credit", "state taxes", "EITC", "refund", "working", "income"],
    },
    # -----------------------------------------------------------------------
    # California-specific programs
    # -----------------------------------------------------------------------
    {
        "id": "caleitc",
        "name": "California EITC (CalEITC) + Young Child Tax Credit",
        "short_name": "CalEITC / YCTC",
        "category": "tax_credit",
        "description": (
            "California's Earned Income Tax Credit (CalEITC) is worth up to $3,529 for families with 3+ children. "
            "The Young Child Tax Credit (YCTC) adds up to $1,117 per child under age 6. "
            "Both are refundable — you get cash even if you owe no taxes."
        ),
        "eligibility": {
            "gross_income_pct_fpl": None,
            "max_income_dollars": 30931,  # 2023 tax year (3+ children)
            "asset_limit_dollars": None,
            "citizenship": "must have valid SSN or ITIN",
            "age_requirement": "YCTC: must have child under age 6",
            "special_rules": [
                "California only",
                "ITIN filers (undocumented immigrants) qualify for CalEITC — unlike federal EITC",
                "CalEITC max: $255 (no children) to $3,529 (3+ children) for 2023 tax year",
                "YCTC: up to $1,117 per qualifying child under 6",
                "Foster Youth Tax Credit also available for former foster youth",
            ],
        },
        "avg_benefit": {
            "family": "Up to $3,529 CalEITC + $1,117/child YCTC; combined often $1,000-$4,500+",
        },
        "apply_url": "https://www.ftb.ca.gov/file/personal/credits/california-earned-income-tax-credit.html",
        "how_to_apply": "Claim on your California state tax return (Form 3514)",
        "portal_steps": [
            "File your California state tax return",
            "Complete Form 3514 (CalEITC)",
            "Include YCTC if you have a child under 6",
            "Use CalFile (free) at ftb.ca.gov or a VITA site",
        ],
        "timeline": "Refund typically within 2-3 weeks of e-filing",
        "tags": ["california", "taxes", "tax credit", "refund", "EITC", "working", "child", "ITIN"],
    },
    {
        "id": "ca_sdi",
        "name": "California SDI / Paid Family Leave",
        "short_name": "CA SDI / PFL",
        "category": "cash_assistance",
        "description": (
            "California's State Disability Insurance (SDI) pays 60-70% of wages for workers unable to work "
            "due to non-work illness, injury, or pregnancy. Paid Family Leave (PFL) pays for bonding with a new child "
            "or caring for a seriously ill family member."
        ),
        "eligibility": {
            "gross_income_pct_fpl": None,
            "asset_limit_dollars": None,
            "citizenship": "must be a California worker who paid SDI taxes",
            "age_requirement": None,
            "special_rules": [
                "California only",
                "Must have earned at least $300 in wages in the base period that SDI taxes were withheld",
                "SDI: up to 52 weeks for disability (illness, injury, pregnancy recovery)",
                "PFL: up to 8 weeks for bonding or caregiving",
                "Benefit: 60-70% of weekly wages, up to ~$1,620/week (2024)",
                "No employer permission needed to file — it's a worker benefit, not employer-dependent",
            ],
        },
        "avg_benefit": {
            "individual": "60-70% of weekly wages; average ~$750-$1,200/week; up to 52 weeks (SDI) or 8 weeks (PFL)",
        },
        "apply_url": "https://www.edd.ca.gov/disability/",
        "how_to_apply": "File online at SDI Online at edd.ca.gov within 49 days of becoming disabled",
        "portal_steps": [
            "Go to edd.ca.gov/disability",
            "Create or log into your SDI Online account",
            "File a disability claim or PFL claim",
            "Have your doctor or midwife complete their portion of the form",
        ],
        "timeline": "First payment typically within 2-3 weeks; 7-day waiting period for SDI (no waiting for PFL)",
        "tags": ["california", "disability", "paid leave", "pregnancy", "maternity", "family leave", "SDI", "PFL", "wages"],
    },
    # -----------------------------------------------------------------------
    # New York-specific programs
    # -----------------------------------------------------------------------
    {
        "id": "ny_eitc",
        "name": "New York State Earned Income Credit",
        "short_name": "NY Earned Income Credit",
        "category": "tax_credit",
        "description": (
            "New York State's Earned Income Credit equals 30% of the federal EITC, one of the most generous "
            "state supplements in the country. New York City adds an additional 5% of the federal EITC for NYC residents."
        ),
        "eligibility": {
            "gross_income_pct_fpl": None,
            "asset_limit_dollars": None,
            "citizenship": "must qualify for federal EITC; ITIN filers may qualify for NY non-custodial parent EIC",
            "age_requirement": "Same as federal EITC",
            "special_rules": [
                "New York State only",
                "NY state credit = 30% of federal EITC",
                "NYC residents get additional 5% of federal EITC (NYC earned income credit)",
                "Must file NY state tax return (IT-215)",
                "Non-custodial parents may qualify for a separate NY credit",
            ],
        },
        "avg_benefit": {
            "individual": "30% of federal EITC; e.g., if federal EITC = $4,000, NY adds ~$1,200 (+$200 for NYC residents)",
        },
        "apply_url": "https://www.tax.ny.gov/pit/credits/eitc.htm",
        "how_to_apply": "Claim on your New York State tax return (Form IT-215)",
        "portal_steps": [
            "File your federal tax return and claim the EITC",
            "File your New York State tax return",
            "Complete Form IT-215 for the state credit",
            "NYC residents also claim the NYC credit on Form IT-201",
        ],
        "timeline": "Refund typically within 2-4 weeks of e-filing",
        "tags": ["new york", "taxes", "tax credit", "EITC", "refund", "NYC", "state taxes"],
    },
    # -----------------------------------------------------------------------
    # Washington State-specific programs
    # -----------------------------------------------------------------------
    {
        "id": "wa_wftc",
        "name": "Washington Working Families Tax Credit (WFTC)",
        "short_name": "WA Working Families Tax Credit",
        "category": "tax_credit",
        "description": (
            "Washington State's Working Families Tax Credit is a refundable annual credit for low-to-moderate income "
            "workers. Washington has no income tax, so this is a standalone credit paid directly by the state."
        ),
        "eligibility": {
            "gross_income_pct_fpl": None,
            "asset_limit_dollars": None,
            "citizenship": "must have a valid SSN or ITIN and live in Washington",
            "age_requirement": "Must meet federal EITC age requirements",
            "special_rules": [
                "Washington State only",
                "Must qualify for and claim the federal EITC",
                "ITIN filers qualify — unlike federal EITC",
                "Credit amount: $315-$1,255 depending on income and number of children",
                "Apply at workingfamiliescredit.wa.gov within 3 years of tax year",
            ],
        },
        "avg_benefit": {
            "individual": "$315 (no children) to $1,255 (3+ children)",
        },
        "apply_url": "https://workingfamiliescredit.wa.gov/",
        "how_to_apply": "Apply online at workingfamiliescredit.wa.gov after filing your federal taxes",
        "portal_steps": [
            "File your federal tax return and claim the EITC",
            "Go to workingfamiliescredit.wa.gov",
            "Create an account and submit your WFTC application",
            "Provide your federal tax return information",
            "Receive payment by check or direct deposit",
        ],
        "timeline": "Applications processed within 3-4 months; apply year-round",
        "tags": ["washington", "taxes", "tax credit", "refund", "EITC", "ITIN", "working families"],
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
    "childcare": {"label": "Child Care", "icon": "👶", "color": "pink"},
}
