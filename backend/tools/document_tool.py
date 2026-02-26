"""
Document analysis tool using Nova Lite vision.
Extracts structured information from uploaded documents like pay stubs,
medical records, utility bills, and benefit letters.
"""

import base64
import json
from typing import Any


DOCUMENT_ANALYSIS_PROMPT = """You are analyzing a document to extract key information for benefit eligibility determination.

Document type: {document_type}

Please extract and return a JSON object with ALL of the following fields (use null if not found):
{{
  "document_type_detected": "pay_stub | tax_return | utility_bill | medical_record | id_document | benefit_letter | lease | bank_statement | other",
  "key_fields": {{
    "name": "full name of person",
    "date": "most recent date on document (YYYY-MM-DD format)",
    "employer_name": "employer or organization name if applicable",
    "gross_income": "gross/total income amount as number (no symbols)",
    "gross_income_period": "weekly | biweekly | monthly | annual",
    "net_income": "net/take-home income as number if shown",
    "address": "street address if present",
    "city_state_zip": "city, state, zip if present",
    "account_number": "masked account/ID number if shown",
    "benefit_amount": "any benefit or payment amount as number",
    "balance_due": "any amount owed or balance due",
    "service_dates": "any service period or pay period dates",
    "ssn_last4": "last 4 of SSN if visible (XXXX format only)",
    "household_members": "list any names that suggest household members"
  }},
  "annual_income_estimate": "estimated annual gross income as a number (null if cannot determine)",
  "income_frequency": "how often income is received",
  "relevant_programs": ["list of benefit programs this document is most relevant to"],
  "flags": ["any important observations like 'recent job loss', 'self-employed', 'multiple income sources'"],
  "confidence": "high | medium | low",
  "summary": "one sentence summary of what this document shows"
}}

Be precise with numbers — do not include $ symbols or commas in numeric fields.
If a field truly cannot be determined, use null.
Return only valid JSON, nothing else."""


def analyze_document(
    image_base64: str,
    document_type: str = "unknown",
    nova_lite_client=None,
) -> dict[str, Any]:
    """
    Analyze an uploaded document using Nova Lite vision.

    Args:
        image_base64: Base64-encoded image data
        document_type: Hint about document type ('pay_stub', 'utility_bill', etc.)
        nova_lite_client: Nova Lite service instance (injected at runtime)

    Returns:
        Structured dict with extracted document fields
    """
    if nova_lite_client is None:
        # Import here to avoid circular dependency
        from backend.services.nova_lite import NovaLiteService
        nova_lite_client = NovaLiteService()

    prompt = DOCUMENT_ANALYSIS_PROMPT.format(document_type=document_type)

    try:
        result = nova_lite_client.analyze_image(
            image_base64=image_base64,
            prompt=prompt,
            expect_json=True,
        )

        if isinstance(result, dict):
            return _post_process(result, document_type)
        else:
            # Try to parse if returned as string
            parsed = json.loads(result)
            return _post_process(parsed, document_type)

    except Exception as e:
        return {
            "error": str(e),
            "document_type_detected": document_type,
            "key_fields": {},
            "annual_income_estimate": None,
            "confidence": "low",
            "summary": "Could not analyze document. Please try again or enter your information manually.",
        }


def _post_process(data: dict, original_type: str) -> dict:
    """Normalize and enrich extracted data."""
    key_fields = data.get("key_fields", {})

    # Estimate annual income from extracted fields
    annual_income = data.get("annual_income_estimate")
    if annual_income is None:
        gross = key_fields.get("gross_income")
        period = key_fields.get("gross_income_period", "")
        if gross:
            try:
                gross_num = float(str(gross).replace(",", "").replace("$", ""))
                multipliers = {
                    "weekly": 52, "biweekly": 26, "semi_monthly": 24,
                    "monthly": 12, "annual": 1, "yearly": 1,
                }
                multiplier = multipliers.get(period.lower(), 12)
                annual_income = gross_num * multiplier
                data["annual_income_estimate"] = round(annual_income, 2)
            except (ValueError, TypeError):
                pass

    # Add useful_for_programs field
    doc_type = data.get("document_type_detected", original_type)
    data["useful_for_programs"] = _infer_relevant_programs(doc_type, data)

    # Privacy: ensure we're not logging SSNs
    if "ssn_last4" in key_fields and key_fields["ssn_last4"]:
        key_fields["ssn_last4"] = "****"  # mask it

    return data


def _infer_relevant_programs(doc_type: str, data: dict) -> list[str]:
    """Infer which benefit programs this document is useful for."""
    relevant = []
    doc_type = doc_type.lower()

    if doc_type in ("pay_stub", "tax_return", "bank_statement"):
        relevant.extend(["SNAP", "Medicaid", "TANF", "EITC", "LIHEAP", "Section 8"])
    if doc_type in ("utility_bill",):
        relevant.extend(["LIHEAP", "Section 8"])
    if doc_type in ("medical_record",):
        relevant.extend(["Medicaid", "SSI", "Medicare Savings"])
    if doc_type in ("id_document",):
        relevant.extend(["All programs requiring ID verification"])
    if doc_type in ("benefit_letter",):
        relevant.extend(["Related program enrollment verification"])
    if doc_type in ("lease",):
        relevant.extend(["Section 8", "TANF", "LIHEAP"])

    return list(set(relevant))
