"""Loan Product Catalog Tools — Stage 3: Loan Exploration.

Provides access to the loan products database for browsing
available products and getting detailed product information.
"""

from ..db import fetch_all, fetch_one


def get_loan_products() -> dict:
    """Get a summary of all available Citibank UK loan products.

    Returns a list of active loan products with key details including
    APR ranges, borrowing limits, and main features.
    """
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
