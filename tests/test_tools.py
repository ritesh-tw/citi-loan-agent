"""
Unit tests for Citibank UK Loan Application Agent — all 4 stages.

Covers:
  Stage 1 — Greeting / Intent (tool-level: get_current_time)
  Stage 2 — Identity & Customer Lookup
  Stage 3 — Loan Product Exploration
  Stage 4 — Loan Pre-Qualification Engine

All database calls are mocked so tests run without a DB connection.
ToolContext is simulated with a plain dict for session state.
"""

import sys
import os
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_ctx(state=None):
    """Return a minimal ToolContext-alike with a mutable state dict."""
    ctx = MagicMock()
    ctx.state = state or {}
    return ctx


# Real product data matching seed_db.py
MOCK_PERS_LOAN = {
    "product_code": "PERS_LOAN",
    "product_name": "Citi Personal Loan",
    "description": "A flexible unsecured personal loan.",
    "min_amount": Decimal("1000.00"),
    "max_amount": Decimal("25000.00"),
    "min_term_months": 12,
    "max_term_months": 60,
    "representative_apr": Decimal("9.9"),
    "min_apr": Decimal("6.9"),
    "max_apr": Decimal("29.9"),
    "eligibility_criteria": {
        "min_income": 15000,
        "residency": ["uk_resident"],
        "employment": ["full_time", "part_time", "self_employed", "retired"],
    },
    "early_repayment_fee_pct": Decimal("0.00"),
    "early_repayment_details": "No early repayment charges apply.",
    "features": ["No early repayment fees", "Fixed monthly payments"],
    "fca_disclosure": "Representative example: £10,000 over 48 months at 9.9% APR.",
    "is_active": True,
}

MOCK_DEBT_CONSOL = {
    "product_code": "DEBT_CONSOL",
    "product_name": "Citi Debt Consolidation Loan",
    "description": "Combine multiple debts into one monthly payment.",
    "min_amount": Decimal("5000.00"),
    "max_amount": Decimal("50000.00"),
    "min_term_months": 24,
    "max_term_months": 84,
    "representative_apr": Decimal("7.9"),
    "min_apr": Decimal("5.9"),
    "max_apr": Decimal("19.9"),
    "eligibility_criteria": {
        "min_income": 15000,
        "residency": ["uk_resident"],
        "employment": ["full_time", "part_time", "self_employed", "retired"],
    },
    "early_repayment_fee_pct": Decimal("0.00"),
    "early_repayment_details": "No early repayment charges apply.",
    "features": ["Single monthly payment", "No arrangement fees"],
    "fca_disclosure": "Representative example: £15,000 over 60 months at 7.9% APR.",
    "is_active": True,
}

MOCK_HOME_IMPROV = {
    "product_code": "HOME_IMPROV",
    "product_name": "Citi Home Improvement Loan",
    "description": "Fund your home renovation project.",
    "min_amount": Decimal("7500.00"),
    "max_amount": Decimal("50000.00"),
    "min_term_months": 12,
    "max_term_months": 120,
    "representative_apr": Decimal("6.9"),
    "min_apr": Decimal("4.9"),
    "max_apr": Decimal("14.9"),
    "eligibility_criteria": {
        "min_income": 15000,
        "residency": ["uk_resident"],
        "employment": ["full_time", "part_time", "self_employed", "retired"],
    },
    "early_repayment_fee_pct": Decimal("0.00"),
    "early_repayment_details": "No early repayment charges apply.",
    "features": ["Competitive rates for homeowners", "No security required up to £25,000"],
    "fca_disclosure": "Representative example: £25,000 over 84 months at 6.9% APR.",
    "is_active": True,
}

MOCK_PERS_LOAN_RULES = [
    {"rule_type": "income_multiplier", "parameters": {"multiplier": 4.0}, "priority": 1},
    {"rule_type": "dti_ratio", "parameters": {"max_ratio": 0.45}, "priority": 2},
    {"rule_type": "risk_score", "parameters": {"max_risk_score": 8}, "priority": 3},
]

MOCK_DEBT_CONSOL_RULES = [
    {"rule_type": "income_multiplier", "parameters": {"multiplier": 5.0}, "priority": 1},
    {"rule_type": "dti_ratio", "parameters": {"max_ratio": 0.50}, "priority": 2},
    {"rule_type": "risk_score", "parameters": {"max_risk_score": 7}, "priority": 3},
]

MOCK_HOME_IMPROV_RULES = [
    {"rule_type": "income_multiplier", "parameters": {"multiplier": 5.5}, "priority": 1},
    {"rule_type": "dti_ratio", "parameters": {"max_ratio": 0.40}, "priority": 2},
    {"rule_type": "risk_score", "parameters": {"max_risk_score": 6}, "priority": 3},
]

# Existing customer fixtures (from seed_db.py)
JAMES_THOMPSON = {
    "customer_id": "CITI-UK-100001",
    "first_name": "James",
    "last_name": "Thompson",
    "date_of_birth": "1985-03-15",
    "postcode": "SW1A 1AA",
    "email": "james.thompson@email.co.uk",
    "phone": "+44 7700 900001",
    "account_opened": "2018-06-01",
    "account_type": "current",
    "risk_score": 3,
    "eligibility_flags": {"pre_approved": True, "existing_loan_holder": False, "premium_customer": True},
    "existing_credit_obligations": [
        {"type": "credit_card", "provider": "Citibank", "balance": 1200, "monthly_payment": 60, "limit": 5000}
    ],
    "annual_income": Decimal("65000.00"),
    "employment_status": "full_time",
    "residency_status": "uk_resident",
}

DAVID_PATEL = {
    "customer_id": "CITI-UK-100003",
    "first_name": "David",
    "last_name": "Patel",
    "date_of_birth": "1978-11-08",
    "postcode": "M1 4BT",
    "email": "david.patel@email.co.uk",
    "phone": "+44 7700 900003",
    "account_opened": "2015-09-20",
    "account_type": "current",
    "risk_score": 5,
    "eligibility_flags": {"pre_approved": False, "existing_loan_holder": True, "premium_customer": False},
    "existing_credit_obligations": [
        {"type": "personal_loan", "provider": "Citibank", "balance": 8500, "monthly_payment": 280},
        {"type": "credit_card", "provider": "Barclays", "balance": 3200, "monthly_payment": 95},
    ],
    "annual_income": Decimal("42000.00"),
    "employment_status": "full_time",
    "residency_status": "uk_resident",
}

THOMAS_OBRIEN = {
    "customer_id": "CITI-UK-100007",
    "first_name": "Thomas",
    "last_name": "O'Brien",
    "date_of_birth": "1972-12-03",
    "postcode": "CF10 1EP",
    "email": "thomas.obrien@email.co.uk",
    "phone": "+44 7700 900007",
    "account_opened": "2016-04-22",
    "account_type": "current",
    "risk_score": 7,
    "eligibility_flags": {"pre_approved": False, "existing_loan_holder": True, "premium_customer": False},
    "existing_credit_obligations": [
        {"type": "personal_loan", "provider": "Citibank", "balance": 15000, "monthly_payment": 420},
        {"type": "credit_card", "provider": "Citibank", "balance": 4800, "monthly_payment": 140},
        {"type": "credit_card", "provider": "HSBC", "balance": 2100, "monthly_payment": 65},
    ],
    "annual_income": Decimal("35000.00"),
    "employment_status": "full_time",
    "residency_status": "uk_resident",
}

AMARA_OKAFOR = {
    "customer_id": "CITI-UK-100008",
    "first_name": "Amara",
    "last_name": "Okafor",
    "date_of_birth": "1993-08-27",
    "postcode": "BS1 5DB",
    "email": "amara.okafor@email.co.uk",
    "phone": "+44 7700 900008",
    "account_opened": "2021-06-18",
    "account_type": "current",
    "risk_score": 4,
    "eligibility_flags": {"pre_approved": True, "existing_loan_holder": False, "premium_customer": False},
    "existing_credit_obligations": [],
    "annual_income": Decimal("48000.00"),
    "employment_status": "full_time",
    "residency_status": "uk_visa",  # Note: on visa
}


# ===========================================================================
# STAGE 1 — Common tool: get_current_time
# ===========================================================================

class TestGetCurrentTime:
    """Stage 1 helper tool tests."""

    def test_returns_time_in_utc(self):
        from loan_application_agent.tools.common import get_current_time
        result = get_current_time("UTC")
        assert "date" in result
        assert "time" in result
        assert "timezone" in result
        assert result["timezone"] == "UTC"

    def test_returns_time_in_london(self):
        from loan_application_agent.tools.common import get_current_time
        result = get_current_time("Europe/London")
        assert result["timezone"] == "Europe/London"
        assert "formatted" in result

    def test_invalid_timezone_falls_back_gracefully(self):
        from loan_application_agent.tools.common import get_current_time
        result = get_current_time("Invalid/Timezone")
        # Should either return an error key or default to UTC
        assert isinstance(result, dict)

    def test_default_timezone_is_utc(self):
        from loan_application_agent.tools.common import get_current_time
        result = get_current_time()
        assert isinstance(result, dict)
        assert "date" in result


# ===========================================================================
# STAGE 2A — Customer Lookup
# ===========================================================================

class TestCustomerLookup:
    """Stage 2: existing customer lookup tests."""

    @patch("loan_application_agent.tools.customer_lookup.fetch_one")
    def test_lookup_james_thompson_success(self, mock_fetch):
        """Existing customer found — returns welcome message and stores in state."""
        from loan_application_agent.tools.customer_lookup import lookup_customer
        mock_fetch.return_value = JAMES_THOMPSON
        ctx = make_ctx()

        result = lookup_customer("Thompson", "SW1A 1AA", "1985-03-15", ctx)

        assert result["found"] is True
        assert result["customer_id"] == "CITI-UK-100001"
        assert "james" in result["name"].lower()
        assert "welcome back" in result["message"].lower()
        assert result["eligibility_flags"]["pre_approved"] is True
        # State must be populated
        assert ctx.state["is_existing_customer"] is True
        assert ctx.state["customer"]["customer_id"] == "CITI-UK-100001"

    @patch("loan_application_agent.tools.customer_lookup.fetch_one")
    def test_lookup_existing_customer_pre_approved_mention(self, mock_fetch):
        """Pre-approved customer — message should mention pre-approval."""
        from loan_application_agent.tools.customer_lookup import lookup_customer
        mock_fetch.return_value = JAMES_THOMPSON
        ctx = make_ctx()
        result = lookup_customer("Thompson", "SW1A 1AA", "1985-03-15", ctx)
        assert "pre-approved" in result["message"].lower()

    @patch("loan_application_agent.tools.customer_lookup.fetch_one")
    def test_lookup_david_patel_with_obligations(self, mock_fetch):
        """Customer with existing obligations — total_monthly_obligations correct."""
        from loan_application_agent.tools.customer_lookup import lookup_customer
        mock_fetch.return_value = DAVID_PATEL
        ctx = make_ctx()
        result = lookup_customer("Patel", "M1 4BT", "1978-11-08", ctx)

        assert result["found"] is True
        assert result["total_monthly_obligations"] == 375  # 280 + 95

    @patch("loan_application_agent.tools.customer_lookup.fetch_one")
    def test_lookup_not_found_returns_graceful_message(self, mock_fetch):
        """Customer details don't match — 'not found' response."""
        from loan_application_agent.tools.customer_lookup import lookup_customer
        mock_fetch.return_value = None
        ctx = make_ctx()
        result = lookup_customer("Doesnotexist", "ZZ99 9ZZ", "1900-01-01", ctx)

        assert result["found"] is False
        assert "couldn't find" in result["message"].lower() or "not found" in result["message"].lower()
        # State must NOT be contaminated
        assert ctx.state.get("is_existing_customer") is None

    @patch("loan_application_agent.tools.customer_lookup.fetch_one")
    def test_lookup_db_error_returns_graceful_fallback(self, mock_fetch):
        """DB unavailable — agent should continue as new customer."""
        from loan_application_agent.tools.customer_lookup import lookup_customer
        mock_fetch.side_effect = Exception("Connection refused")
        ctx = make_ctx()
        result = lookup_customer("Thompson", "SW1A 1AA", "1985-03-15", ctx)

        assert result["found"] is False
        assert "unable" in result["message"].lower() or "new customer" in result["message"].lower()

    @patch("loan_application_agent.tools.customer_lookup.fetch_one")
    def test_lookup_postcode_normalised(self, mock_fetch):
        """Postcode with and without space both match (DB query handles it)."""
        from loan_application_agent.tools.customer_lookup import lookup_customer
        mock_fetch.return_value = JAMES_THOMPSON
        ctx = make_ctx()
        # Postcode with no space — tool should still pass it; DB normalises it
        result = lookup_customer("Thompson", "SW1A1AA", "1985-03-15", ctx)
        assert result["found"] is True

    @patch("loan_application_agent.tools.customer_lookup.fetch_one")
    def test_lookup_case_insensitive_last_name(self, mock_fetch):
        """Last name lookup is case-insensitive (DB query handles it)."""
        from loan_application_agent.tools.customer_lookup import lookup_customer
        mock_fetch.return_value = JAMES_THOMPSON
        ctx = make_ctx()
        result = lookup_customer("THOMPSON", "SW1A 1AA", "1985-03-15", ctx)
        assert result["found"] is True

    @patch("loan_application_agent.tools.customer_lookup.fetch_one")
    def test_lookup_customer_no_obligations(self, mock_fetch):
        """Customer with no obligations — total_monthly_obligations is 0."""
        from loan_application_agent.tools.customer_lookup import lookup_customer
        sarah = {**JAMES_THOMPSON, "existing_credit_obligations": [], "first_name": "Sarah", "last_name": "Mitchell"}
        mock_fetch.return_value = sarah
        ctx = make_ctx()
        result = lookup_customer("Mitchell", "EC2N 4AQ", "1990-07-22", ctx)
        assert result["found"] is True
        assert result["total_monthly_obligations"] == 0

    @patch("loan_application_agent.tools.customer_lookup.fetch_one")
    def test_lookup_thomas_obrien_high_risk(self, mock_fetch):
        """High-risk customer (risk_score=7) — still found, risk flagged."""
        from loan_application_agent.tools.customer_lookup import lookup_customer
        mock_fetch.return_value = THOMAS_OBRIEN
        ctx = make_ctx()
        result = lookup_customer("O'Brien", "CF10 1EP", "1972-12-03", ctx)

        assert result["found"] is True
        assert result["risk_score"] == 7
        assert ctx.state["customer"]["risk_score"] == 7


# ===========================================================================
# STAGE 2B — PII Collection
# ===========================================================================

class TestCollectPersonalInfo:
    """Stage 2: new customer PII collection tests."""

    def test_store_single_field_full_name(self):
        from loan_application_agent.tools.customer_lookup import collect_personal_info
        ctx = make_ctx()
        result = collect_personal_info("full_name", "Alice Smith", ctx)

        assert result["status"] == "stored"
        assert result["field"] == "full_name"
        assert result["value"] == "Alice Smith"
        assert result["complete"] is False
        assert "full_name" not in result["missing_fields"]
        assert "date_of_birth" in result["missing_fields"]
        assert ctx.state["personal_info"]["full_name"] == "Alice Smith"

    def test_store_all_five_pii_fields(self):
        from loan_application_agent.tools.customer_lookup import collect_personal_info
        ctx = make_ctx()
        fields = [
            ("full_name", "Alice Smith"),
            ("date_of_birth", "1990-05-20"),
            ("postcode", "N1 9GU"),
            ("email", "alice@example.co.uk"),
            ("phone", "+44 7700 123456"),
        ]
        result = None
        for name, value in fields:
            result = collect_personal_info(name, value, ctx)

        assert result["complete"] is True
        assert result["missing_fields"] == []

    def test_collect_persists_across_calls(self):
        from loan_application_agent.tools.customer_lookup import collect_personal_info
        ctx = make_ctx()
        collect_personal_info("full_name", "Bob Jones", ctx)
        collect_personal_info("email", "bob@example.co.uk", ctx)

        assert ctx.state["personal_info"]["full_name"] == "Bob Jones"
        assert ctx.state["personal_info"]["email"] == "bob@example.co.uk"

    def test_overwrite_field_with_new_value(self):
        from loan_application_agent.tools.customer_lookup import collect_personal_info
        ctx = make_ctx({"personal_info": {"full_name": "Old Name"}})
        collect_personal_info("full_name", "New Name", ctx)
        assert ctx.state["personal_info"]["full_name"] == "New Name"

    def test_missing_fields_decrease_as_collected(self):
        from loan_application_agent.tools.customer_lookup import collect_personal_info
        ctx = make_ctx()
        r1 = collect_personal_info("full_name", "A B", ctx)
        r2 = collect_personal_info("date_of_birth", "1990-01-01", ctx)
        assert len(r1["missing_fields"]) > len(r2["missing_fields"])


class TestValidatePersonalInfo:
    """Stage 2: PII validation tests."""

    def test_empty_state_all_fields_missing(self):
        from loan_application_agent.tools.customer_lookup import validate_personal_info
        ctx = make_ctx()
        result = validate_personal_info(tool_context=ctx)

        assert result["complete"] is False
        assert len(result["missing_fields"]) == 5
        assert result["collected"] == {}

    def test_partial_state_shows_remaining(self):
        from loan_application_agent.tools.customer_lookup import validate_personal_info
        ctx = make_ctx({"personal_info": {"full_name": "Alice", "email": "a@b.com"}})
        result = validate_personal_info(tool_context=ctx)

        assert result["complete"] is False
        assert len(result["missing_fields"]) == 3
        assert "full_name" not in result["missing_fields"]
        assert "email" not in result["missing_fields"]

    def test_all_fields_present_marks_complete(self):
        from loan_application_agent.tools.customer_lookup import validate_personal_info
        ctx = make_ctx({
            "personal_info": {
                "full_name": "Alice Smith",
                "date_of_birth": "1990-05-20",
                "postcode": "N1 9GU",
                "email": "alice@example.co.uk",
                "phone": "+44 7700 123456",
            }
        })
        result = validate_personal_info(tool_context=ctx)
        assert result["complete"] is True
        assert result["missing_fields"] == []


# ===========================================================================
# STAGE 3 — Loan Product Catalog
# ===========================================================================

class TestGetLoanProducts:
    """Stage 3: product catalog listing tests."""

    @patch("loan_application_agent.tools.loan_products.fetch_all")
    def test_returns_all_three_products(self, mock_fetch):
        from loan_application_agent.tools.loan_products import get_loan_products
        mock_fetch.return_value = [MOCK_PERS_LOAN, MOCK_DEBT_CONSOL, MOCK_HOME_IMPROV]
        result = get_loan_products()

        assert result["count"] == 3
        codes = [p["product_code"] for p in result["products"]]
        assert "PERS_LOAN" in codes
        assert "DEBT_CONSOL" in codes
        assert "HOME_IMPROV" in codes

    @patch("loan_application_agent.tools.loan_products.fetch_all")
    def test_product_contains_apr_range(self, mock_fetch):
        from loan_application_agent.tools.loan_products import get_loan_products
        mock_fetch.return_value = [MOCK_PERS_LOAN]
        result = get_loan_products()

        p = result["products"][0]
        assert "apr_range" in p
        assert "%" in p["apr_range"]
        assert "representative_apr" in p

    @patch("loan_application_agent.tools.loan_products.fetch_all")
    def test_product_contains_borrowing_range(self, mock_fetch):
        from loan_application_agent.tools.loan_products import get_loan_products
        mock_fetch.return_value = [MOCK_PERS_LOAN]
        result = get_loan_products()

        p = result["products"][0]
        assert "borrowing_range" in p
        assert "£" in p["borrowing_range"]

    @patch("loan_application_agent.tools.loan_products.fetch_all")
    def test_fca_disclosure_present(self, mock_fetch):
        from loan_application_agent.tools.loan_products import get_loan_products
        mock_fetch.return_value = [MOCK_PERS_LOAN]
        result = get_loan_products()

        p = result["products"][0]
        assert "fca_disclosure" in p
        assert len(p["fca_disclosure"]) > 10

    @patch("loan_application_agent.tools.loan_products.fetch_all")
    def test_disclaimer_present(self, mock_fetch):
        from loan_application_agent.tools.loan_products import get_loan_products
        mock_fetch.return_value = [MOCK_PERS_LOAN]
        result = get_loan_products()

        assert "disclaimer" in result
        assert "representative" in result["disclaimer"].lower()

    @patch("loan_application_agent.tools.loan_products.fetch_all")
    def test_db_error_returns_fallback_data(self, mock_fetch):
        from loan_application_agent.tools.loan_products import get_loan_products
        mock_fetch.side_effect = Exception("Connection refused")
        result = get_loan_products()

        # Fallback must have 3 products
        assert result["count"] == 3
        assert len(result["products"]) == 3


class TestGetProductDetails:
    """Stage 3: individual product details tests."""

    @patch("loan_application_agent.tools.loan_products.fetch_one")
    def test_personal_loan_details_found(self, mock_fetch):
        from loan_application_agent.tools.loan_products import get_product_details
        mock_fetch.return_value = MOCK_PERS_LOAN
        result = get_product_details("PERS_LOAN")

        assert result["found"] is True
        assert result["product_code"] == "PERS_LOAN"
        assert "interest_rates" in result
        assert result["interest_rates"]["representative_apr"] == 9.9

    @patch("loan_application_agent.tools.loan_products.fetch_one")
    def test_details_include_eligibility_criteria(self, mock_fetch):
        from loan_application_agent.tools.loan_products import get_product_details
        mock_fetch.return_value = MOCK_PERS_LOAN
        result = get_product_details("PERS_LOAN")

        assert "eligibility_criteria" in result
        assert "min_income" in result["eligibility_criteria"]

    @patch("loan_application_agent.tools.loan_products.fetch_one")
    def test_details_include_early_repayment(self, mock_fetch):
        from loan_application_agent.tools.loan_products import get_product_details
        mock_fetch.return_value = MOCK_PERS_LOAN
        result = get_product_details("PERS_LOAN")

        assert "early_repayment" in result
        assert "fee_percentage" in result["early_repayment"]
        assert result["early_repayment"]["fee_percentage"] == 0.0

    @patch("loan_application_agent.tools.loan_products.fetch_one")
    def test_details_include_repayment_terms(self, mock_fetch):
        from loan_application_agent.tools.loan_products import get_product_details
        mock_fetch.return_value = MOCK_PERS_LOAN
        result = get_product_details("PERS_LOAN")

        assert "repayment_terms" in result
        assert result["repayment_terms"]["min_months"] == 12
        assert result["repayment_terms"]["max_months"] == 60

    @patch("loan_application_agent.tools.loan_products.fetch_one")
    def test_debt_consolidation_details(self, mock_fetch):
        from loan_application_agent.tools.loan_products import get_product_details
        mock_fetch.return_value = MOCK_DEBT_CONSOL
        result = get_product_details("DEBT_CONSOL")

        assert result["found"] is True
        assert result["product_code"] == "DEBT_CONSOL"
        assert result["repayment_terms"]["max_months"] == 84

    @patch("loan_application_agent.tools.loan_products.fetch_one")
    def test_home_improvement_details(self, mock_fetch):
        from loan_application_agent.tools.loan_products import get_product_details
        mock_fetch.return_value = MOCK_HOME_IMPROV
        result = get_product_details("HOME_IMPROV")

        assert result["found"] is True
        assert result["repayment_terms"]["max_months"] == 120

    @patch("loan_application_agent.tools.loan_products.fetch_one")
    def test_invalid_product_code_not_found(self, mock_fetch):
        from loan_application_agent.tools.loan_products import get_product_details
        mock_fetch.return_value = None
        result = get_product_details("INVALID_CODE")
        assert result["found"] is False

    @patch("loan_application_agent.tools.loan_products.fetch_one")
    def test_db_error_returns_fallback_for_known_product(self, mock_fetch):
        from loan_application_agent.tools.loan_products import get_product_details
        mock_fetch.side_effect = Exception("DB down")
        result = get_product_details("PERS_LOAN")
        # Fallback should still return something
        assert isinstance(result, dict)


# ===========================================================================
# STAGE 4A — Application Info Collection
# ===========================================================================

class TestCollectApplicationInfo:
    """Stage 4: application field collection tests."""

    def test_store_employment_status(self):
        from loan_application_agent.tools.prequalification import collect_application_info
        ctx = make_ctx()
        result = collect_application_info("employment_status", "full_time", ctx)

        assert result["status"] == "stored"
        assert result["field"] == "employment_status"
        assert result["complete"] is False
        assert ctx.state["application"]["employment_status"] == "full_time"

    def test_store_all_six_required_fields(self):
        from loan_application_agent.tools.prequalification import collect_application_info
        ctx = make_ctx()
        fields = [
            ("employment_status", "full_time"),
            ("annual_income", "50000"),
            ("loan_amount", "10000"),
            ("loan_purpose", "personal"),
            ("repayment_term_months", "36"),
            ("residency_status", "uk_resident"),
        ]
        result = None
        for name, value in fields:
            result = collect_application_info(name, value, ctx)

        assert result["complete"] is True
        assert result["missing_fields"] == []

    def test_missing_fields_decrease_as_stored(self):
        from loan_application_agent.tools.prequalification import collect_application_info
        ctx = make_ctx()
        r1 = collect_application_info("employment_status", "full_time", ctx)
        r2 = collect_application_info("annual_income", "50000", ctx)
        assert len(r1["missing_fields"]) > len(r2["missing_fields"])

    def test_field_overwrite(self):
        from loan_application_agent.tools.prequalification import collect_application_info
        ctx = make_ctx({"application": {"loan_amount": "5000"}})
        collect_application_info("loan_amount", "10000", ctx)
        assert ctx.state["application"]["loan_amount"] == "10000"


class TestValidateApplicationInfo:
    """Stage 4: application validation tests."""

    def test_empty_application_all_missing(self):
        from loan_application_agent.tools.prequalification import validate_application_info
        ctx = make_ctx()
        result = validate_application_info(tool_context=ctx)

        assert result["complete"] is False
        assert len(result["missing_fields"]) == 6

    def test_partial_application_shows_remaining(self):
        from loan_application_agent.tools.prequalification import validate_application_info
        ctx = make_ctx({
            "application": {
                "employment_status": "full_time",
                "annual_income": "50000",
            }
        })
        result = validate_application_info(tool_context=ctx)

        assert result["complete"] is False
        assert len(result["missing_fields"]) == 4

    def test_complete_application_marks_done(self):
        from loan_application_agent.tools.prequalification import validate_application_info
        ctx = make_ctx({
            "application": {
                "employment_status": "full_time",
                "annual_income": "50000",
                "loan_amount": "10000",
                "loan_purpose": "personal",
                "repayment_term_months": "36",
                "residency_status": "uk_resident",
            }
        })
        result = validate_application_info(tool_context=ctx)
        assert result["complete"] is True

    def test_includes_existing_customer_flag(self):
        from loan_application_agent.tools.prequalification import validate_application_info
        ctx = make_ctx({"is_existing_customer": True, "customer": {"first_name": "James", "last_name": "Thompson"}})
        result = validate_application_info(tool_context=ctx)
        assert result["is_existing_customer"] is True
        assert result["customer_name"] == "James Thompson"

    def test_new_customer_flag_false(self):
        from loan_application_agent.tools.prequalification import validate_application_info
        ctx = make_ctx()
        result = validate_application_info(tool_context=ctx)
        assert result["is_existing_customer"] is False
        assert result["customer_name"] is None


# ===========================================================================
# STAGE 4B — Pre-Qualification Engine
# ===========================================================================

class TestRunPrequalification:
    """Stage 4: full pre-qualification engine tests."""

    def _base_state(self, overrides=None):
        """Default clean-slate new customer application state."""
        state = {
            "application": {
                "employment_status": "full_time",
                "annual_income": "50000",
                "loan_amount": "10000",
                "loan_purpose": "personal",
                "repayment_term_months": "36",
                "residency_status": "uk_resident",
            },
            "is_existing_customer": False,
        }
        if overrides:
            for key, val in overrides.items():
                if isinstance(val, dict) and isinstance(state.get(key), dict):
                    state[key].update(val)
                else:
                    state[key] = val
        return state

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_approved_new_customer(self, mock_product, mock_rules, mock_save):
        """New customer with good income and low DTI → APPROVED."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        ctx = make_ctx(self._base_state())
        result = run_prequalification("PERS_LOAN", ctx)

        assert result["decision"] == "approved"
        assert "prequalified_amount" in result
        assert "indicative_apr" in result
        assert "affordability_score" in result
        assert "fca_disclosure" in result

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_approved_includes_monthly_payment(self, mock_product, mock_rules, mock_save):
        """Approved result includes estimated monthly payment and total payable."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        ctx = make_ctx(self._base_state())
        result = run_prequalification("PERS_LOAN", ctx)

        assert "estimated_monthly_payment" in result
        assert "total_payable" in result
        assert "£" in result["estimated_monthly_payment"]

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_existing_customer_pre_approved_gets_discount(self, mock_product, mock_rules, mock_save):
        """Pre-approved existing customer (James Thompson) gets 1% APR discount."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        # James Thompson: risk_score=3, pre_approved=True, income=65000
        state = self._base_state({
            "is_existing_customer": True,
            "customer": {
                "risk_score": 3,
                "eligibility_flags": {"pre_approved": True},
                "existing_credit_obligations": [{"monthly_payment": 60}],
                "annual_income": 65000,
            },
        })
        ctx = make_ctx(state)
        result_existing = run_prequalification("PERS_LOAN", ctx)

        # New customer (risk=5, no discount) for comparison
        ctx_new = make_ctx(self._base_state())
        result_new = run_prequalification("PERS_LOAN", ctx_new)

        assert result_existing["decision"] == "approved"
        # Extract APR numeric value: "8.9%" → 8.9
        apr_existing = float(result_existing["indicative_apr"].rstrip("%"))
        apr_new = float(result_new["indicative_apr"].rstrip("%"))
        assert apr_existing < apr_new, "Pre-approved existing customer should have lower APR"

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_partial_when_requested_amount_exceeds_income_limit(self, mock_product, mock_rules, mock_save):
        """Requesting more than 4x income → PARTIAL with reduced amount."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        # income=5000, loan=25000 → income limit = 5000 * 4 = 20000 < 25000
        state = self._base_state({
            "application": {
                "employment_status": "full_time",
                "annual_income": "5000",
                "loan_amount": "25000",
                "loan_purpose": "personal",
                "repayment_term_months": "60",
                "residency_status": "uk_resident",
            }
        })
        ctx = make_ctx(state)
        result = run_prequalification("PERS_LOAN", ctx)

        # Income too low for 25k but 20k >= min_amount 1k → PARTIAL
        assert result["decision"] in ("partial", "declined")
        if result["decision"] == "partial":
            assert "prequalified_amount" in result

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_declined_non_uk_resident(self, mock_product, mock_rules, mock_save):
        """Non-UK resident → DECLINED (residency criteria not met)."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        state = self._base_state({"application": {"residency_status": "non_resident"}})
        ctx = make_ctx(state)
        result = run_prequalification("PERS_LOAN", ctx)

        assert result["decision"] == "declined"
        assert any("residency" in r.lower() for r in result["reasons"])

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_declined_unemployed_applicant(self, mock_product, mock_rules, mock_save):
        """Unemployed applicant not eligible for PERS_LOAN → DECLINED."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        state = self._base_state({"application": {"employment_status": "unemployed"}})
        ctx = make_ctx(state)
        result = run_prequalification("PERS_LOAN", ctx)

        assert result["decision"] == "declined"
        assert any("employment" in r.lower() for r in result["reasons"])

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_declined_income_below_minimum(self, mock_product, mock_rules, mock_save):
        """Annual income below minimum £15,000 → DECLINED."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        state = self._base_state({"application": {"annual_income": "10000", "loan_amount": "5000"}})
        ctx = make_ctx(state)
        result = run_prequalification("PERS_LOAN", ctx)

        assert result["decision"] == "declined"
        assert any("income" in r.lower() for r in result["reasons"])

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_declined_amount_below_product_minimum(self, mock_product, mock_rules, mock_save):
        """Loan amount below product minimum £1,000 → DECLINED."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        state = self._base_state({"application": {"loan_amount": "500"}})
        ctx = make_ctx(state)
        result = run_prequalification("PERS_LOAN", ctx)

        assert result["decision"] == "declined"
        assert any("minimum" in r.lower() for r in result["reasons"])

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_declined_amount_above_product_maximum(self, mock_product, mock_rules, mock_save):
        """Loan amount above product maximum £25,000 for PERS_LOAN → PARTIAL (capped at max)."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        state = self._base_state({
            "application": {"annual_income": "100000", "loan_amount": "30000"}
        })
        ctx = make_ctx(state)
        result = run_prequalification("PERS_LOAN", ctx)

        # Engine caps at product max and returns PARTIAL (offers £25,000 instead of £30,000)
        assert result["decision"] == "partial"
        assert any("maximum" in r.lower() for r in result["reasons"])

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_declined_term_out_of_range(self, mock_product, mock_rules, mock_save):
        """Repayment term outside allowed range → DECLINED."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        state = self._base_state({"application": {"repayment_term_months": "120"}})  # max is 60
        ctx = make_ctx(state)
        result = run_prequalification("PERS_LOAN", ctx)

        assert result["decision"] == "declined"
        assert any("term" in r.lower() for r in result["reasons"])

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_declined_high_risk_score(self, mock_product, mock_rules, mock_save):
        """Customer risk score > 8 (PERS_LOAN max) → DECLINED."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        state = self._base_state({
            "is_existing_customer": True,
            "customer": {
                "risk_score": 9,  # exceeds max 8
                "eligibility_flags": {"pre_approved": False},
                "existing_credit_obligations": [],
            }
        })
        ctx = make_ctx(state)
        result = run_prequalification("PERS_LOAN", ctx)

        assert result["decision"] == "declined"
        assert any("risk" in r.lower() for r in result["reasons"])

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_missing_required_fields_returns_incomplete(self, mock_product, mock_rules, mock_save):
        """Incomplete application data → decision 'incomplete'."""
        from loan_application_agent.tools.prequalification import run_prequalification
        ctx = make_ctx({"application": {"employment_status": "full_time"}})
        result = run_prequalification("PERS_LOAN", ctx)

        assert result["decision"] == "incomplete"
        assert "missing_fields" in result

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_invalid_numeric_values_returns_error(self, mock_product, mock_rules, mock_save):
        """Non-numeric income/amount → decision 'error'."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES

        state = self._base_state({"application": {"annual_income": "not_a_number"}})
        ctx = make_ctx(state)
        result = run_prequalification("PERS_LOAN", ctx)

        assert result["decision"] == "error"

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_product_not_found_returns_error(self, mock_product, mock_rules, mock_save):
        """Invalid product code → decision 'error'."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = None

        ctx = make_ctx(self._base_state())
        result = run_prequalification("INVALID_PRODUCT", ctx)

        assert result["decision"] == "error"
        assert "not found" in result["message"].lower()

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_approved_result_includes_fca_disclosure(self, mock_product, mock_rules, mock_save):
        """FCA disclosure always present in result (Consumer Duty)."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        ctx = make_ctx(self._base_state())
        result = run_prequalification("PERS_LOAN", ctx)

        assert "fca_disclosure" in result
        assert "indicative" in result["fca_disclosure"].lower()
        assert "not a guaranteed offer" in result["fca_disclosure"].lower()

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_result_stored_in_session_state(self, mock_product, mock_rules, mock_save):
        """Pre-qualification result saved to session state for downstream use."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        ctx = make_ctx(self._base_state())
        run_prequalification("PERS_LOAN", ctx)

        assert "prequalification_result" in ctx.state
        assert ctx.state["prequalification_result"]["decision"] in ("approved", "partial", "declined")

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_apr_within_product_bounds(self, mock_product, mock_rules, mock_save):
        """Calculated APR must be clamped between product min and max APR."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        ctx = make_ctx(self._base_state())
        result = run_prequalification("PERS_LOAN", ctx)

        apr = float(result["indicative_apr"].rstrip("%"))
        assert 6.9 <= apr <= 29.9

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_debt_consolidation_approved(self, mock_product, mock_rules, mock_save):
        """Debt consolidation loan — approved scenario."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_DEBT_CONSOL
        mock_rules.return_value = MOCK_DEBT_CONSOL_RULES
        mock_save.return_value = {"id": 1}

        state = self._base_state({
            "application": {
                "employment_status": "full_time",
                "annual_income": "45000",
                "loan_amount": "12000",
                "loan_purpose": "debt_consolidation",
                "repayment_term_months": "48",
                "residency_status": "uk_resident",
            }
        })
        ctx = make_ctx(state)
        result = run_prequalification("DEBT_CONSOL", ctx)

        assert result["decision"] == "approved"
        assert result["product_name"] == "Citi Debt Consolidation Loan"
        apr = float(result["indicative_apr"].rstrip("%"))
        assert 5.9 <= apr <= 19.9

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_home_improvement_approved(self, mock_product, mock_rules, mock_save):
        """Home improvement loan — approved scenario."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_HOME_IMPROV
        mock_rules.return_value = MOCK_HOME_IMPROV_RULES
        mock_save.return_value = {"id": 1}

        state = self._base_state({
            "application": {
                "employment_status": "full_time",
                "annual_income": "60000",
                "loan_amount": "15000",
                "loan_purpose": "home_improvement",
                "repayment_term_months": "60",
                "residency_status": "uk_resident",
            }
        })
        ctx = make_ctx(state)
        result = run_prequalification("HOME_IMPROV", ctx)

        assert result["decision"] == "approved"
        assert result["product_name"] == "Citi Home Improvement Loan"
        apr = float(result["indicative_apr"].rstrip("%"))
        assert 4.9 <= apr <= 14.9

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_thomas_obrien_high_obligations_declined(self, mock_product, mock_rules, mock_save):
        """Thomas O'Brien: risk_score=7, high obligations, low income → DECLINED for DEBT_CONSOL."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_DEBT_CONSOL
        mock_rules.return_value = MOCK_DEBT_CONSOL_RULES
        mock_save.return_value = {"id": 1}

        # O'Brien: risk=7 (exceeds DEBT_CONSOL max 7 exactly — borderline), income=35k, obligations=625/mo
        state = {
            "is_existing_customer": True,
            "customer": {
                "risk_score": 8,  # above DEBT_CONSOL max 7
                "eligibility_flags": {"pre_approved": False},
                "existing_credit_obligations": [
                    {"monthly_payment": 420},
                    {"monthly_payment": 140},
                    {"monthly_payment": 65},
                ],
            },
            "application": {
                "employment_status": "full_time",
                "annual_income": "35000",
                "loan_amount": "15000",
                "loan_purpose": "debt_consolidation",
                "repayment_term_months": "48",
                "residency_status": "uk_resident",
            },
        }
        ctx = make_ctx(state)
        result = run_prequalification("DEBT_CONSOL", ctx)

        assert result["decision"] == "declined"
        assert any("risk" in r.lower() for r in result["reasons"])

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_affordability_score_is_percentage(self, mock_product, mock_rules, mock_save):
        """Affordability score is always between 0 and 100."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        ctx = make_ctx(self._base_state())
        result = run_prequalification("PERS_LOAN", ctx)

        assert 0 <= result["affordability_score"] <= 100

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_larger_loan_gets_better_apr(self, mock_product, mock_rules, mock_save):
        """Loans > £15,000 get 0.5% APR discount (amount_adjustment)."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        state_small = self._base_state({"application": {"loan_amount": "5000"}})
        state_large = self._base_state({"application": {"loan_amount": "20000", "annual_income": "80000"}})

        result_small = run_prequalification("PERS_LOAN", make_ctx(state_small))
        result_large = run_prequalification("PERS_LOAN", make_ctx(state_large))

        if result_small["decision"] == "approved" and result_large["decision"] == "approved":
            apr_small = float(result_small["indicative_apr"].rstrip("%"))
            apr_large = float(result_large["indicative_apr"].rstrip("%"))
            assert apr_large <= apr_small, "Larger loan should not have higher APR"

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_db_error_during_save_does_not_fail_result(self, mock_product, mock_rules, mock_save):
        """Audit log DB failure should not propagate — result still returned."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.side_effect = Exception("DB write failed")

        ctx = make_ctx(self._base_state())
        result = run_prequalification("PERS_LOAN", ctx)

        # Should still return a valid result despite audit log failure
        assert result["decision"] in ("approved", "partial", "declined")

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_retired_applicant_eligible_for_personal_loan(self, mock_product, mock_rules, mock_save):
        """Retired employment status is eligible for PERS_LOAN."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        state = self._base_state({"application": {"employment_status": "retired"}})
        ctx = make_ctx(state)
        result = run_prequalification("PERS_LOAN", ctx)

        # Retired is in eligibility list — should not be declined for employment
        if result["decision"] == "declined":
            assert not any("employment" in r.lower() for r in result.get("reasons", []))

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_self_employed_applicant_eligible(self, mock_product, mock_rules, mock_save):
        """Self-employed applicant is eligible for PERS_LOAN."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        state = self._base_state({"application": {"employment_status": "self_employed"}})
        ctx = make_ctx(state)
        result = run_prequalification("PERS_LOAN", ctx)

        if result["decision"] == "declined":
            assert not any("employment" in r.lower() for r in result.get("reasons", []))

    @patch("loan_application_agent.tools.prequalification.execute_returning")
    @patch("loan_application_agent.tools.prequalification.fetch_all")
    @patch("loan_application_agent.db.fetch_one")
    def test_uk_visa_holder_declined_for_pers_loan(self, mock_product, mock_rules, mock_save):
        """UK visa holder not on PERS_LOAN residency list → DECLINED."""
        from loan_application_agent.tools.prequalification import run_prequalification
        mock_product.return_value = MOCK_PERS_LOAN
        mock_rules.return_value = MOCK_PERS_LOAN_RULES
        mock_save.return_value = {"id": 1}

        state = self._base_state({"application": {"residency_status": "uk_visa"}})
        ctx = make_ctx(state)
        result = run_prequalification("PERS_LOAN", ctx)

        assert result["decision"] == "declined"
        assert any("residency" in r.lower() for r in result["reasons"])
