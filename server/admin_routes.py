"""Admin API routes for managing loan application data.

Provides CRUD endpoints for customers, loan products,
pre-qualification rules, results audit log, and admin config.
"""

import json
from datetime import datetime, date
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from loan_application_agent.db import fetch_all, fetch_one, execute, execute_returning

router = APIRouter(prefix="/api/admin", tags=["admin"])


# --- JSON serialization helper ---

def _serialize(obj):
    """Convert DB row values to JSON-safe types."""
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


# ====== STATS ======

@router.get("/stats")
async def get_stats():
    """Dashboard statistics."""
    customers = fetch_one("SELECT COUNT(*) as count FROM customers")
    products = fetch_one("SELECT COUNT(*) as count FROM loan_products WHERE is_active = TRUE")
    results = fetch_one("SELECT COUNT(*) as count FROM prequalification_results")
    approved = fetch_one("SELECT COUNT(*) as count FROM prequalification_results WHERE decision = 'approved'")
    total = results["count"] if results else 0
    return {
        "total_customers": customers["count"] if customers else 0,
        "active_products": products["count"] if products else 0,
        "total_prequalifications": total,
        "approval_rate": round((approved["count"] / total * 100) if total > 0 else 0, 1),
    }


# ====== CUSTOMERS ======

@router.get("/customers")
async def list_customers():
    """List all customers."""
    rows = fetch_all(
        """SELECT id, customer_id, first_name, last_name, date_of_birth, postcode,
                  email, phone, account_type, risk_score, eligibility_flags,
                  existing_credit_obligations, annual_income, employment_status,
                  residency_status, account_opened
           FROM customers ORDER BY id"""
    )
    return {"customers": [_serialize(r) for r in rows]}


class CustomerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    postcode: str | None = None
    email: str | None = None
    phone: str | None = None
    risk_score: int | None = None
    annual_income: float | None = None
    employment_status: str | None = None
    residency_status: str | None = None
    eligibility_flags: dict | None = None
    existing_credit_obligations: list | None = None


@router.put("/customers/{customer_id}")
async def update_customer(customer_id: int, data: CustomerUpdate):
    """Update a customer record."""
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")

    set_clauses = []
    params = []
    for key, value in updates.items():
        if key in ("eligibility_flags", "existing_credit_obligations"):
            set_clauses.append(f"{key} = %s")
            params.append(json.dumps(value))
        else:
            set_clauses.append(f"{key} = %s")
            params.append(value)

    set_clauses.append("updated_at = NOW()")
    params.append(customer_id)

    execute(
        f"UPDATE customers SET {', '.join(set_clauses)} WHERE id = %s",
        tuple(params),
    )
    return {"status": "updated", "id": customer_id}


class CustomerCreate(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    date_of_birth: str
    postcode: str
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    account_type: str = "current"
    risk_score: int = 5
    annual_income: float | None = None
    employment_status: str | None = None
    residency_status: str = "uk_resident"
    eligibility_flags: dict | None = None
    existing_credit_obligations: list | None = None


@router.post("/customers")
async def create_customer(data: CustomerCreate):
    """Create a new customer."""
    result = execute_returning(
        """INSERT INTO customers (
            customer_id, first_name, last_name, date_of_birth, postcode,
            email, phone, address, account_opened, account_type,
            risk_score, annual_income, employment_status, residency_status,
            eligibility_flags, existing_credit_obligations
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s,%s,%s,%s,%s,%s,%s)
        RETURNING id""",
        (
            data.customer_id, data.first_name, data.last_name,
            data.date_of_birth, data.postcode, data.email, data.phone,
            data.address, data.account_type, data.risk_score,
            data.annual_income, data.employment_status, data.residency_status,
            json.dumps(data.eligibility_flags or {}),
            json.dumps(data.existing_credit_obligations or []),
        ),
    )
    return {"status": "created", "id": result["id"] if result else None}


@router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: int):
    """Delete a customer."""
    execute("DELETE FROM customers WHERE id = %s", (customer_id,))
    return {"status": "deleted", "id": customer_id}


# ====== LOAN PRODUCTS ======

@router.get("/loan-products")
async def list_loan_products():
    """List all loan products."""
    rows = fetch_all("SELECT * FROM loan_products ORDER BY id")
    return {"products": [_serialize(r) for r in rows]}


class LoanProductUpdate(BaseModel):
    product_name: str | None = None
    description: str | None = None
    min_amount: float | None = None
    max_amount: float | None = None
    min_term_months: int | None = None
    max_term_months: int | None = None
    representative_apr: float | None = None
    min_apr: float | None = None
    max_apr: float | None = None
    eligibility_criteria: dict | None = None
    early_repayment_fee_pct: float | None = None
    early_repayment_details: str | None = None
    features: list | None = None
    fca_disclosure: str | None = None
    is_active: bool | None = None


@router.put("/loan-products/{product_id}")
async def update_loan_product(product_id: int, data: LoanProductUpdate):
    """Update a loan product."""
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")

    set_clauses = []
    params = []
    for key, value in updates.items():
        if key in ("eligibility_criteria", "features"):
            set_clauses.append(f"{key} = %s")
            params.append(json.dumps(value))
        else:
            set_clauses.append(f"{key} = %s")
            params.append(value)

    set_clauses.append("updated_at = NOW()")
    params.append(product_id)

    execute(
        f"UPDATE loan_products SET {', '.join(set_clauses)} WHERE id = %s",
        tuple(params),
    )
    return {"status": "updated", "id": product_id}


class LoanProductCreate(BaseModel):
    product_code: str
    product_name: str
    description: str = ""
    min_amount: float = 1000
    max_amount: float = 50000
    min_term_months: int = 12
    max_term_months: int = 60
    representative_apr: float = 5.0
    min_apr: float = 3.0
    max_apr: float = 25.0
    eligibility_criteria: dict | None = None
    early_repayment_fee_pct: float = 0.0
    early_repayment_details: str = ""
    features: list | None = None
    fca_disclosure: str = ""
    is_active: bool = True


@router.post("/loan-products")
async def create_loan_product(data: LoanProductCreate):
    """Create a new loan product."""
    result = execute_returning(
        """INSERT INTO loan_products (
            product_code, product_name, description, min_amount, max_amount,
            min_term_months, max_term_months, representative_apr, min_apr, max_apr,
            eligibility_criteria, early_repayment_fee_pct, early_repayment_details,
            features, fca_disclosure, is_active
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id""",
        (
            data.product_code, data.product_name, data.description,
            data.min_amount, data.max_amount, data.min_term_months,
            data.max_term_months, data.representative_apr, data.min_apr,
            data.max_apr, json.dumps(data.eligibility_criteria or {}),
            data.early_repayment_fee_pct, data.early_repayment_details,
            json.dumps(data.features or []), data.fca_disclosure, data.is_active,
        ),
    )
    return {"status": "created", "id": result["id"] if result else None}


@router.delete("/loan-products/{product_id}")
async def delete_loan_product(product_id: int):
    """Delete a loan product."""
    execute("DELETE FROM loan_products WHERE id = %s", (product_id,))
    return {"status": "deleted", "id": product_id}


# ====== PRE-QUALIFICATION RULES ======

@router.get("/prequalification-rules")
async def list_prequalification_rules():
    """List all pre-qualification rules."""
    rows = fetch_all(
        """SELECT r.*, p.product_name
           FROM prequalification_rules r
           LEFT JOIN loan_products p ON r.product_code = p.product_code
           ORDER BY r.product_code, r.priority"""
    )
    return {"rules": [_serialize(r) for r in rows]}


class PrequalRuleUpdate(BaseModel):
    rule_name: str | None = None
    rule_type: str | None = None
    parameters: dict | None = None
    priority: int | None = None
    is_active: bool | None = None


@router.put("/prequalification-rules/{rule_id}")
async def update_prequalification_rule(rule_id: int, data: PrequalRuleUpdate):
    """Update a pre-qualification rule."""
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")

    set_clauses = []
    params = []
    for key, value in updates.items():
        if key == "parameters":
            set_clauses.append(f"{key} = %s")
            params.append(json.dumps(value))
        else:
            set_clauses.append(f"{key} = %s")
            params.append(value)

    params.append(rule_id)
    execute(
        f"UPDATE prequalification_rules SET {', '.join(set_clauses)} WHERE id = %s",
        tuple(params),
    )
    return {"status": "updated", "id": rule_id}


class PrequalRuleCreate(BaseModel):
    product_code: str
    rule_name: str
    rule_type: str = "threshold"
    parameters: dict | None = None
    priority: int = 1
    is_active: bool = True


@router.post("/prequalification-rules")
async def create_prequalification_rule(data: PrequalRuleCreate):
    """Create a new pre-qualification rule."""
    result = execute_returning(
        """INSERT INTO prequalification_rules (
            product_code, rule_name, rule_type, parameters, priority, is_active
        ) VALUES (%s,%s,%s,%s,%s,%s)
        RETURNING id""",
        (
            data.product_code, data.rule_name, data.rule_type,
            json.dumps(data.parameters or {}), data.priority, data.is_active,
        ),
    )
    return {"status": "created", "id": result["id"] if result else None}


@router.delete("/prequalification-rules/{rule_id}")
async def delete_prequalification_rule(rule_id: int):
    """Delete a pre-qualification rule."""
    execute("DELETE FROM prequalification_rules WHERE id = %s", (rule_id,))
    return {"status": "deleted", "id": rule_id}


# ====== PRE-QUALIFICATION RESULTS ======

@router.get("/prequalification-results")
async def list_prequalification_results():
    """List all pre-qualification results (audit log)."""
    rows = fetch_all(
        """SELECT * FROM prequalification_results ORDER BY created_at DESC LIMIT 100"""
    )
    return {"results": [_serialize(r) for r in rows]}


# ====== ADMIN CONFIG ======

@router.get("/config")
async def list_config():
    """List all admin configuration entries."""
    rows = fetch_all("SELECT * FROM admin_config ORDER BY config_key")
    return {"config": [_serialize(r) for r in rows]}


class ConfigUpdate(BaseModel):
    config_value: dict


@router.put("/config/{config_key}")
async def update_config(config_key: str, data: ConfigUpdate):
    """Update an admin config value."""
    execute(
        "UPDATE admin_config SET config_value = %s, updated_at = NOW() WHERE config_key = %s",
        (json.dumps(data.config_value), config_key),
    )
    return {"status": "updated", "key": config_key}


# ====== SEED/RESET ======

@router.post("/reset-data")
async def reset_data():
    """Re-seed the database with default mock data."""
    from loan_application_agent.seed_db import seed
    seed()
    return {"status": "reset", "message": "Database re-seeded with default data"}
