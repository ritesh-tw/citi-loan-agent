"""Pre-Qualification Tools — Stage 4: Loan Pre-Qualification.

Collects application information and runs the pre-qualification engine
to determine indicative loan offers based on customer data and rules.
"""

import json
from decimal import Decimal

from google.adk.tools import ToolContext

from ..db import fetch_all, execute_returning

REQUIRED_FIELDS = [
    "employment_status",
    "annual_income",
    "loan_amount",
    "loan_purpose",
    "repayment_term_months",
    "residency_status",
]


def collect_application_info(
    field_name: str,
    field_value: str,
    tool_context: ToolContext,
) -> dict:
    """Store a piece of loan application information collected from the user.

    Args:
        field_name: The field being collected. Must be one of:
            employment_status (full_time, part_time, self_employed, retired, unemployed),
            annual_income (yearly income in GBP as a number),
            loan_amount (requested loan amount in GBP as a number),
            loan_purpose (personal, debt_consolidation, home_improvement, car, holiday, wedding, other),
            repayment_term_months (desired repayment period in months as a number),
            residency_status (uk_resident, uk_visa, non_resident).
        field_value: The value provided by the user.

    Returns:
        Confirmation of stored field and remaining required fields.
    """
    application = tool_context.state.get("application", {})
    application[field_name] = field_value
    tool_context.state["application"] = application

    missing = [f for f in REQUIRED_FIELDS if f not in application]
    return {
        "status": "stored",
        "field": field_name,
        "value": field_value,
        "missing_fields": missing,
        "complete": len(missing) == 0,
    }


def validate_application_info(tool_context: ToolContext) -> dict:
    """Check which required fields are still needed for the loan application.

    Returns the current application data, missing fields, and completion status.
    """
    application = tool_context.state.get("application", {})
    missing = [f for f in REQUIRED_FIELDS if f not in application]
    customer = tool_context.state.get("customer", {})

    return {
        "collected": dict(application),
        "missing_fields": missing,
        "complete": len(missing) == 0,
        "is_existing_customer": tool_context.state.get("is_existing_customer", False),
        "customer_name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or None,
    }


def run_prequalification(
    product_code: str,
    tool_context: ToolContext,
) -> dict:
    """Run the pre-qualification engine for a specific loan product.

    This evaluates the user's application data against the product's
    pre-qualification rules and returns an indicative offer.

    Args:
        product_code: The loan product to pre-qualify for
            (PERS_LOAN, DEBT_CONSOL, or HOME_IMPROV).

    Returns:
        Pre-qualification result including indicative offer,
        affordability score, and FCA disclosure.
    """
    application = tool_context.state.get("application", {})
    customer = tool_context.state.get("customer", {})
    is_existing = tool_context.state.get("is_existing_customer", False)

    # Validate completeness
    missing = [f for f in REQUIRED_FIELDS if f not in application]
    if missing:
        return {
            "decision": "incomplete",
            "message": f"Cannot run pre-qualification. Missing fields: {', '.join(missing)}",
            "missing_fields": missing,
        }

    # Parse application values
    try:
        annual_income = float(application["annual_income"])
        loan_amount = float(application["loan_amount"])
        term_months = int(application["repayment_term_months"])
    except (ValueError, TypeError):
        return {
            "decision": "error",
            "message": "Invalid numeric values in application. Please provide valid numbers for income, loan amount, and repayment term.",
        }

    employment_status = application["employment_status"]
    residency_status = application["residency_status"]
    risk_score = customer.get("risk_score", 5) if is_existing else 5

    # Get existing monthly obligations
    existing_obligations = customer.get("existing_credit_obligations", [])
    total_monthly_obligations = sum(
        ob.get("monthly_payment", 0) for ob in existing_obligations
    )

    # Fetch product details and rules
    from ..db import fetch_one
    product = fetch_one(
        "SELECT * FROM loan_products WHERE product_code = %s AND is_active = TRUE",
        (product_code.upper(),),
    )
    if not product:
        return {"decision": "error", "message": f"Product '{product_code}' not found or inactive."}

    rules = fetch_all(
        "SELECT * FROM prequalification_rules WHERE product_code = %s AND is_active = TRUE ORDER BY priority",
        (product_code.upper(),),
    )

    # Run pre-qualification engine
    decline_reasons = []
    max_borrowing = float(product["max_amount"])

    for rule in rules:
        params = rule["parameters"]
        rule_type = rule["rule_type"]

        if rule_type == "income_multiplier":
            multiplier = params.get("multiplier", 4.0)
            income_limit = annual_income * multiplier
            max_borrowing = min(max_borrowing, income_limit)
            if loan_amount > income_limit:
                decline_reasons.append(
                    f"Requested amount exceeds maximum based on income (£{income_limit:,.0f})"
                )

        elif rule_type == "dti_ratio":
            max_ratio = params.get("max_ratio", 0.45)
            monthly_income = annual_income / 12
            # Estimate new loan monthly payment (simplified)
            estimated_monthly = loan_amount / term_months
            total_dti = (total_monthly_obligations + estimated_monthly) / monthly_income
            if total_dti > max_ratio:
                decline_reasons.append(
                    f"Debt-to-income ratio ({total_dti:.0%}) exceeds maximum ({max_ratio:.0%})"
                )

        elif rule_type == "risk_score":
            max_risk = params.get("max_risk_score", 8)
            if risk_score > max_risk:
                decline_reasons.append(
                    f"Risk assessment score ({risk_score}) exceeds threshold"
                )

    # Check product-level eligibility
    criteria = product["eligibility_criteria"]
    if residency_status not in criteria.get("residency", ["uk_resident"]):
        decline_reasons.append("Residency status does not meet product requirements")

    if employment_status not in criteria.get("employment", []):
        decline_reasons.append(f"Employment status '{employment_status}' not eligible for this product")

    if annual_income < criteria.get("min_income", 0):
        decline_reasons.append(
            f"Annual income below minimum requirement of £{criteria.get('min_income', 0):,.0f}"
        )

    if loan_amount < float(product["min_amount"]):
        decline_reasons.append(f"Amount below minimum of £{product['min_amount']:,.0f}")

    if loan_amount > float(product["max_amount"]):
        decline_reasons.append(f"Amount above maximum of £{product['max_amount']:,.0f}")

    if term_months < product["min_term_months"] or term_months > product["max_term_months"]:
        decline_reasons.append(
            f"Term must be between {product['min_term_months']} and {product['max_term_months']} months"
        )

    # Calculate results
    prequalified_amount = min(loan_amount, max_borrowing)
    prequalified_amount = max(prequalified_amount, float(product["min_amount"]))

    # Calculate indicative APR based on risk and amount
    base_apr = float(product["representative_apr"])
    risk_adjustment = (risk_score - 3) * 0.5  # lower risk = lower rate
    amount_adjustment = 0
    if loan_amount > 15000:
        amount_adjustment = -0.5  # slightly better rates for larger loans
    indicative_apr = max(
        float(product["min_apr"]),
        min(float(product["max_apr"]), base_apr + risk_adjustment + amount_adjustment),
    )

    # Existing customer discount
    if is_existing and customer.get("eligibility_flags", {}).get("pre_approved"):
        indicative_apr = max(float(product["min_apr"]), indicative_apr - 1.0)

    # Calculate affordability score (0-100)
    monthly_income = annual_income / 12
    estimated_monthly_payment = loan_amount / term_months
    affordability_ratio = (total_monthly_obligations + estimated_monthly_payment) / monthly_income
    affordability_score = max(0, min(100, int((1 - affordability_ratio) * 100)))

    # Determine decision
    if decline_reasons:
        if prequalified_amount >= float(product["min_amount"]) and prequalified_amount < loan_amount:
            decision = "partial"
        else:
            decision = "declined"
            prequalified_amount = 0
    else:
        decision = "approved"

    # Calculate monthly payment for prequalified amount
    if prequalified_amount > 0:
        # Simple interest calculation for display
        monthly_rate = indicative_apr / 100 / 12
        if monthly_rate > 0:
            monthly_payment = prequalified_amount * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
        else:
            monthly_payment = prequalified_amount / term_months
        total_payable = monthly_payment * term_months
    else:
        monthly_payment = 0
        total_payable = 0

    # Save result to DB
    result_data = {
        "session_id": tool_context.state.get("session_id", "unknown"),
        "customer_id": customer.get("customer_id"),
        "product_code": product_code.upper(),
        "requested_amount": loan_amount,
        "prequalified_amount": prequalified_amount,
        "indicative_apr": indicative_apr,
        "affordability_score": affordability_score,
        "decision": decision,
        "decline_reasons": decline_reasons,
        "input_data": {
            "application": application,
            "is_existing_customer": is_existing,
            "risk_score": risk_score,
            "total_monthly_obligations": total_monthly_obligations,
        },
    }

    try:
        execute_returning(
            """
            INSERT INTO prequalification_results
                (session_id, customer_id, product_code, requested_amount,
                 prequalified_amount, indicative_apr, affordability_score,
                 decision, decline_reasons, input_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                result_data["session_id"],
                result_data["customer_id"],
                result_data["product_code"],
                result_data["requested_amount"],
                result_data["prequalified_amount"],
                result_data["indicative_apr"],
                result_data["affordability_score"],
                result_data["decision"],
                json.dumps(result_data["decline_reasons"]),
                json.dumps(result_data["input_data"]),
            ),
        )
    except Exception:
        pass  # Don't fail the tool if audit logging fails

    # Store result in session state
    tool_context.state["prequalification_result"] = result_data

    # Build response
    response = {
        "decision": decision,
        "product_name": product["product_name"],
        "requested_amount": f"£{loan_amount:,.0f}",
        "indicative_apr": f"{indicative_apr:.1f}%",
        "affordability_score": affordability_score,
    }

    if decision == "approved":
        response.update({
            "prequalified_amount": f"£{prequalified_amount:,.0f}",
            "estimated_monthly_payment": f"£{monthly_payment:,.2f}",
            "total_payable": f"£{total_payable:,.2f}",
            "repayment_term": f"{term_months} months",
            "message": (
                f"Great news! You are pre-qualified for a {product['product_name']} "
                f"of £{prequalified_amount:,.0f} at an indicative rate of {indicative_apr:.1f}% APR."
            ),
        })
    elif decision == "partial":
        response.update({
            "prequalified_amount": f"£{prequalified_amount:,.0f}",
            "estimated_monthly_payment": f"£{monthly_payment:,.2f}",
            "total_payable": f"£{total_payable:,.2f}",
            "repayment_term": f"{term_months} months",
            "reasons": decline_reasons,
            "message": (
                f"Based on our assessment, we can offer you a {product['product_name']} "
                f"of up to £{prequalified_amount:,.0f} at an indicative rate of {indicative_apr:.1f}% APR. "
                f"This is less than your requested amount of £{loan_amount:,.0f}."
            ),
        })
    else:
        response.update({
            "reasons": decline_reasons,
            "message": (
                "Unfortunately, we are unable to pre-qualify you for this product at this time. "
                "This does not necessarily mean you would be declined for a loan — "
                "we encourage you to explore our other products or speak with an advisor."
            ),
        })

    response["fca_disclosure"] = (
        "Important: This is an indicative quote based on the information you have provided. "
        "It is not a guaranteed offer of credit. A formal application will require a full "
        "credit check, which may affect your credit score. The final rate and terms offered "
        "may differ from this indication. Citibank UK is authorised and regulated by the "
        "Financial Conduct Authority."
    )

    return response
