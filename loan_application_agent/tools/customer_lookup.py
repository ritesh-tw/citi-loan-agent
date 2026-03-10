"""Customer Lookup & PII Collection Tools — Stage 2: Identity & Customer Status Check.

Searches the customers database to verify existing Citibank UK customers
using last name, postcode, and date of birth.
Also collects personal information from new customers.
"""

from google.adk.tools import ToolContext

from ..db import fetch_one

REQUIRED_PII_FIELDS = ["full_name", "date_of_birth", "postcode", "email", "phone"]


def collect_personal_info(
    field_name: str,
    field_value: str,
    tool_context: ToolContext,
) -> dict:
    """Store personal information collected from a new customer.

    Args:
        field_name: The field being collected. Must be one of:
            full_name (first and last name),
            date_of_birth (in DD/MM/YYYY or YYYY-MM-DD format),
            postcode (UK postcode),
            email (email address),
            phone (phone number).
        field_value: The value provided by the user.

    Returns:
        Confirmation of stored field and remaining required fields.
    """
    personal_info = tool_context.state.get("personal_info", {})
    personal_info[field_name] = field_value
    tool_context.state["personal_info"] = personal_info

    missing = [f for f in REQUIRED_PII_FIELDS if f not in personal_info]
    return {
        "status": "stored",
        "field": field_name,
        "value": field_value,
        "missing_fields": missing,
        "complete": len(missing) == 0,
    }


def validate_personal_info(tool_context: ToolContext) -> dict:
    """Check which personal information fields are still needed from the user.

    Returns the current collected data, missing fields, and completion status.
    """
    personal_info = tool_context.state.get("personal_info", {})
    missing = [f for f in REQUIRED_PII_FIELDS if f not in personal_info]
    return {
        "collected": dict(personal_info),
        "missing_fields": missing,
        "complete": len(missing) == 0,
    }


def lookup_customer(
    last_name: str,
    postcode: str,
    date_of_birth: str,
    tool_context: ToolContext,
) -> dict:
    """Look up an existing Citibank UK customer by their last name, postcode, and date of birth.

    Args:
        last_name: Customer's last name (case-insensitive).
        postcode: UK postcode (e.g. 'SW1A 1AA').
        date_of_birth: Date of birth in YYYY-MM-DD format (e.g. '1985-03-15').

    Returns:
        Customer details if found, or a not-found message.
    """
    row = fetch_one(
        """
        SELECT customer_id, first_name, last_name, date_of_birth, postcode,
               email, phone, account_opened, account_type, risk_score,
               eligibility_flags, existing_credit_obligations,
               annual_income, employment_status, residency_status
        FROM customers
        WHERE LOWER(last_name) = LOWER(%s)
          AND UPPER(REPLACE(postcode, ' ', '')) = UPPER(REPLACE(%s, ' ', ''))
          AND date_of_birth = %s
        """,
        (last_name.strip(), postcode.strip(), date_of_birth.strip()),
    )

    if not row:
        return {
            "found": False,
            "message": (
                "We couldn't find a matching customer record. "
                "Please double-check the details, or we can continue "
                "with your application as a new customer."
            ),
        }

    # Store customer in session state for later stages
    customer_data = {
        "customer_id": row["customer_id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "date_of_birth": str(row["date_of_birth"]),
        "postcode": row["postcode"],
        "email": row["email"],
        "phone": row["phone"],
        "account_opened": str(row["account_opened"]),
        "account_type": row["account_type"],
        "risk_score": row["risk_score"],
        "eligibility_flags": row["eligibility_flags"],
        "existing_credit_obligations": row["existing_credit_obligations"],
        "annual_income": float(row["annual_income"]) if row["annual_income"] else None,
        "employment_status": row["employment_status"],
        "residency_status": row["residency_status"],
    }
    tool_context.state["customer"] = customer_data
    tool_context.state["is_existing_customer"] = True

    # Calculate total monthly obligations
    total_monthly = sum(
        ob.get("monthly_payment", 0)
        for ob in (row["existing_credit_obligations"] or [])
    )

    return {
        "found": True,
        "customer_id": row["customer_id"],
        "name": f"{row['first_name']} {row['last_name']}",
        "account_type": row["account_type"],
        "account_opened": str(row["account_opened"]),
        "risk_score": row["risk_score"],
        "eligibility_flags": row["eligibility_flags"],
        "existing_credit_obligations": row["existing_credit_obligations"],
        "total_monthly_obligations": total_monthly,
        "message": (
            f"Welcome back, {row['first_name']}! "
            f"We found your account (opened {row['account_opened']}). "
            f"{'You are pre-approved for select loan products!' if row['eligibility_flags'].get('pre_approved') else ''}"
        ),
    }
