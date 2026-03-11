"""Loan Product Catalog Tools — Stage 3: Loan Exploration.

Provides access to the loan products database for browsing
available products and getting detailed product information.
Includes fallback data when the database is unavailable.
"""

from ..db import fetch_all, fetch_one

_FALLBACK_PRODUCTS = {
    "products": [
        {
            "product_code": "PERS_LOAN",
            "product_name": "Citi Personal Loan",
            "description": "A flexible unsecured personal loan for any purpose — from home improvements to big purchases.",
            "borrowing_range": "£1,000 to £50,000",
            "term_range": "12 to 84 months",
            "representative_apr": "6.9% APR (representative)",
            "apr_range": "3.4% to 21.9%",
            "key_features": ["No early repayment fees", "Fixed monthly payments", "Quick online application", "Funds within 24 hours"],
            "fca_disclosure": "Representative example: If you borrow £10,000 over 48 months at 6.9% APR (representative), your monthly repayment would be £238.71. Total amount payable: £11,458.08.",
        },
        {
            "product_code": "DEBT_CONSOL",
            "product_name": "Citi Debt Consolidation Loan",
            "description": "Simplify your finances by combining multiple debts into one manageable monthly payment.",
            "borrowing_range": "£3,000 to £35,000",
            "term_range": "24 to 60 months",
            "representative_apr": "7.9% APR (representative)",
            "apr_range": "4.9% to 24.9%",
            "key_features": ["Single monthly payment", "Potentially lower overall rate", "Free debt assessment", "No arrangement fees"],
            "fca_disclosure": "Representative example: If you borrow £15,000 over 60 months at 7.9% APR (representative), your monthly repayment would be £302.76. Total amount payable: £18,165.60.",
        },
        {
            "product_code": "HOME_IMPROV",
            "product_name": "Citi Home Improvement Loan",
            "description": "Fund your home renovation or improvement project with a competitive fixed-rate loan.",
            "borrowing_range": "£5,000 to £75,000",
            "term_range": "12 to 120 months",
            "representative_apr": "5.9% APR (representative)",
            "apr_range": "3.1% to 18.9%",
            "key_features": ["Competitive rates for homeowners", "Longer repayment terms available", "No security required up to £25,000", "Free property valuation for larger loans"],
            "fca_disclosure": "Representative example: If you borrow £25,000 over 84 months at 5.9% APR (representative), your monthly repayment would be £363.42. Total amount payable: £30,527.28.",
        },
    ],
    "count": 3,
    "disclaimer": (
        "The rates shown are representative APRs. The actual rate offered "
        "to you will depend on your individual circumstances and credit history. "
        "All loans are subject to status and affordability checks."
    ),
}

_FALLBACK_DETAILS = {p["product_code"]: p for p in _FALLBACK_PRODUCTS["products"]}


def get_loan_products() -> dict:
    """Get a summary of all available Citibank UK loan products.

    Returns a list of active loan products with key details including
    APR ranges, borrowing limits, and main features.
    """
    try:
        rows = fetch_all(
            """
            SELECT product_code, product_name, description,
                   min_amount, max_amount, min_term_months, max_term_months,
                   representative_apr, min_apr, max_apr,
                   features, fca_disclosure
            FROM loan_products
            WHERE is_active = TRUE
            ORDER BY representative_apr ASC
            """
        )
    except Exception:
        return _FALLBACK_PRODUCTS

    products = []
    for r in rows:
        products.append({
            "product_code": r["product_code"],
            "product_name": r["product_name"],
            "description": r["description"],
            "borrowing_range": f"£{r['min_amount']:,.0f} to £{r['max_amount']:,.0f}",
            "term_range": f"{r['min_term_months']} to {r['max_term_months']} months",
            "representative_apr": f"{r['representative_apr']}% APR (representative)",
            "apr_range": f"{r['min_apr']}% to {r['max_apr']}%",
            "key_features": r["features"],
            "fca_disclosure": r["fca_disclosure"],
        })

    return {
        "products": products,
        "count": len(products),
        "disclaimer": (
            "The rates shown are representative APRs. The actual rate offered "
            "to you will depend on your individual circumstances and credit history. "
            "All loans are subject to status and affordability checks."
        ),
    }


def get_product_details(product_code: str) -> dict:
    """Get full details for a specific loan product.

    Args:
        product_code: The product code (e.g. 'PERS_LOAN', 'DEBT_CONSOL', 'HOME_IMPROV').

    Returns:
        Complete product details including eligibility criteria,
        early repayment terms, and FCA disclosure.
    """
    try:
        row = fetch_one(
            """
            SELECT product_code, product_name, description,
                   min_amount, max_amount, min_term_months, max_term_months,
                   representative_apr, min_apr, max_apr,
                   eligibility_criteria, early_repayment_fee_pct,
                   early_repayment_details, features, fca_disclosure
            FROM loan_products
            WHERE product_code = %s AND is_active = TRUE
            """,
            (product_code.upper(),),
        )
    except Exception:
        fallback = _FALLBACK_DETAILS.get(product_code.upper())
        if fallback:
            return {"found": True, **fallback}
        return {"found": False, "message": f"Product '{product_code}' not found."}

    if not row:
        return {
            "found": False,
            "message": f"Product '{product_code}' not found. Please check the product code.",
        }

    return {
        "found": True,
        "product_code": row["product_code"],
        "product_name": row["product_name"],
        "description": row["description"],
        "borrowing_range": {
            "min": float(row["min_amount"]),
            "max": float(row["max_amount"]),
            "formatted": f"£{row['min_amount']:,.0f} to £{row['max_amount']:,.0f}",
        },
        "repayment_terms": {
            "min_months": row["min_term_months"],
            "max_months": row["max_term_months"],
            "formatted": f"{row['min_term_months']} to {row['max_term_months']} months",
        },
        "interest_rates": {
            "representative_apr": float(row["representative_apr"]),
            "min_apr": float(row["min_apr"]),
            "max_apr": float(row["max_apr"]),
            "formatted": f"{row['representative_apr']}% APR (representative)",
        },
        "eligibility_criteria": row["eligibility_criteria"],
        "early_repayment": {
            "fee_percentage": float(row["early_repayment_fee_pct"]),
            "details": row["early_repayment_details"],
        },
        "features": row["features"],
        "fca_disclosure": row["fca_disclosure"],
    }
