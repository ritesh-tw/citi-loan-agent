"""Database schema creation and seed data for Loan Application Agent.

Run: python -m loan_application_agent.seed_db
"""

import json
import psycopg2
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://riteshkumar@localhost:5433/loan_agent"
)

# First connect to finagent to create loan_agent db if needed
ADMIN_DB_URL = os.getenv(
    "ADMIN_DATABASE_URL",
    "postgresql://riteshkumar@localhost:5433/finagent"
)

SCHEMA_SQL = """
-- Customers table: existing Citibank UK customers
CREATE TABLE IF NOT EXISTS customers (
    id                  SERIAL PRIMARY KEY,
    customer_id         VARCHAR(20) UNIQUE NOT NULL,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    date_of_birth       DATE NOT NULL,
    postcode            VARCHAR(10) NOT NULL,
    email               VARCHAR(255),
    phone               VARCHAR(20),
    address             TEXT,
    account_opened      DATE NOT NULL,
    account_type        VARCHAR(50) NOT NULL,
    risk_score          INTEGER CHECK (risk_score BETWEEN 1 AND 10),
    eligibility_flags   JSONB DEFAULT '{}',
    existing_credit_obligations JSONB DEFAULT '[]',
    annual_income       DECIMAL(12,2),
    employment_status   VARCHAR(50),
    residency_status    VARCHAR(50) DEFAULT 'uk_resident',
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_customers_lookup
    ON customers (LOWER(last_name), postcode, date_of_birth);

-- Loan products catalog
CREATE TABLE IF NOT EXISTS loan_products (
    id                      SERIAL PRIMARY KEY,
    product_code            VARCHAR(20) UNIQUE NOT NULL,
    product_name            VARCHAR(100) NOT NULL,
    description             TEXT NOT NULL,
    min_amount              DECIMAL(12,2) NOT NULL,
    max_amount              DECIMAL(12,2) NOT NULL,
    min_term_months         INTEGER NOT NULL,
    max_term_months         INTEGER NOT NULL,
    representative_apr      DECIMAL(5,2) NOT NULL,
    min_apr                 DECIMAL(5,2) NOT NULL,
    max_apr                 DECIMAL(5,2) NOT NULL,
    eligibility_criteria    JSONB NOT NULL,
    early_repayment_fee_pct DECIMAL(5,2) DEFAULT 0,
    early_repayment_details TEXT,
    features                JSONB DEFAULT '[]',
    fca_disclosure          TEXT NOT NULL,
    is_active               BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW()
);

-- Pre-qualification rules
CREATE TABLE IF NOT EXISTS prequalification_rules (
    id              SERIAL PRIMARY KEY,
    product_code    VARCHAR(20) REFERENCES loan_products(product_code),
    rule_name       VARCHAR(100) NOT NULL,
    rule_type       VARCHAR(50) NOT NULL,
    parameters      JSONB NOT NULL,
    priority        INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Pre-qualification results audit log
CREATE TABLE IF NOT EXISTS prequalification_results (
    id                  SERIAL PRIMARY KEY,
    session_id          VARCHAR(100),
    customer_id         VARCHAR(20),
    product_code        VARCHAR(20),
    requested_amount    DECIMAL(12,2),
    prequalified_amount DECIMAL(12,2),
    indicative_apr      DECIMAL(5,2),
    affordability_score INTEGER CHECK (affordability_score BETWEEN 0 AND 100),
    decision            VARCHAR(20) NOT NULL,
    decline_reasons     JSONB DEFAULT '[]',
    input_data          JSONB NOT NULL,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- Admin configuration
CREATE TABLE IF NOT EXISTS admin_config (
    id              SERIAL PRIMARY KEY,
    config_key      VARCHAR(100) UNIQUE NOT NULL,
    config_value    JSONB NOT NULL,
    description     TEXT,
    updated_at      TIMESTAMP DEFAULT NOW(),
    updated_by      VARCHAR(100) DEFAULT 'system'
);
"""

CUSTOMERS = [
    {
        "customer_id": "CITI-UK-100001",
        "first_name": "James",
        "last_name": "Thompson",
        "date_of_birth": "1985-03-15",
        "postcode": "SW1A 1AA",
        "email": "james.thompson@email.co.uk",
        "phone": "+44 7700 900001",
        "address": "12 Westminster Avenue, London SW1A 1AA",
        "account_opened": "2018-06-01",
        "account_type": "current",
        "risk_score": 3,
        "eligibility_flags": {"pre_approved": True, "existing_loan_holder": False, "premium_customer": True},
        "existing_credit_obligations": [
            {"type": "credit_card", "provider": "Citibank", "balance": 1200, "monthly_payment": 60, "limit": 5000}
        ],
        "annual_income": 65000,
        "employment_status": "full_time",
        "residency_status": "uk_resident",
    },
    {
        "customer_id": "CITI-UK-100002",
        "first_name": "Sarah",
        "last_name": "Mitchell",
        "date_of_birth": "1990-07-22",
        "postcode": "EC2N 4AQ",
        "email": "sarah.mitchell@email.co.uk",
        "phone": "+44 7700 900002",
        "address": "45 Bishopsgate, London EC2N 4AQ",
        "account_opened": "2020-01-15",
        "account_type": "both",
        "risk_score": 2,
        "eligibility_flags": {"pre_approved": True, "existing_loan_holder": False, "premium_customer": False},
        "existing_credit_obligations": [],
        "annual_income": 85000,
        "employment_status": "full_time",
        "residency_status": "uk_resident",
    },
    {
        "customer_id": "CITI-UK-100003",
        "first_name": "David",
        "last_name": "Patel",
        "date_of_birth": "1978-11-08",
        "postcode": "M1 4BT",
        "email": "david.patel@email.co.uk",
        "phone": "+44 7700 900003",
        "address": "8 Piccadilly, Manchester M1 4BT",
        "account_opened": "2015-09-20",
        "account_type": "current",
        "risk_score": 5,
        "eligibility_flags": {"pre_approved": False, "existing_loan_holder": True, "premium_customer": False},
        "existing_credit_obligations": [
            {"type": "personal_loan", "provider": "Citibank", "balance": 8500, "monthly_payment": 280, "remaining_months": 30},
            {"type": "credit_card", "provider": "Barclays", "balance": 3200, "monthly_payment": 95, "limit": 8000}
        ],
        "annual_income": 42000,
        "employment_status": "full_time",
        "residency_status": "uk_resident",
    },
    {
        "customer_id": "CITI-UK-100004",
        "first_name": "Emma",
        "last_name": "Williams",
        "date_of_birth": "1995-02-14",
        "postcode": "B1 1BB",
        "email": "emma.williams@email.co.uk",
        "phone": "+44 7700 900004",
        "address": "23 Colmore Row, Birmingham B1 1BB",
        "account_opened": "2022-03-10",
        "account_type": "savings",
        "risk_score": 4,
        "eligibility_flags": {"pre_approved": True, "existing_loan_holder": False, "premium_customer": False},
        "existing_credit_obligations": [
            {"type": "car_finance", "provider": "Ford Credit", "balance": 12000, "monthly_payment": 350, "remaining_months": 24}
        ],
        "annual_income": 38000,
        "employment_status": "full_time",
        "residency_status": "uk_resident",
    },
    {
        "customer_id": "CITI-UK-100005",
        "first_name": "Robert",
        "last_name": "Chen",
        "date_of_birth": "1968-09-30",
        "postcode": "LS1 5DL",
        "email": "robert.chen@email.co.uk",
        "phone": "+44 7700 900005",
        "address": "17 Park Row, Leeds LS1 5DL",
        "account_opened": "2012-11-05",
        "account_type": "both",
        "risk_score": 2,
        "eligibility_flags": {"pre_approved": True, "existing_loan_holder": False, "premium_customer": True},
        "existing_credit_obligations": [],
        "annual_income": 95000,
        "employment_status": "self_employed",
        "residency_status": "uk_resident",
    },
    {
        "customer_id": "CITI-UK-100006",
        "first_name": "Fatima",
        "last_name": "Khan",
        "date_of_birth": "1988-05-19",
        "postcode": "G1 1XQ",
        "email": "fatima.khan@email.co.uk",
        "phone": "+44 7700 900006",
        "address": "55 George Square, Glasgow G1 1XQ",
        "account_opened": "2019-08-12",
        "account_type": "current",
        "risk_score": 3,
        "eligibility_flags": {"pre_approved": False, "existing_loan_holder": False, "premium_customer": False},
        "existing_credit_obligations": [
            {"type": "student_loan", "provider": "SLC", "balance": 22000, "monthly_payment": 120}
        ],
        "annual_income": 52000,
        "employment_status": "full_time",
        "residency_status": "uk_resident",
    },
    {
        "customer_id": "CITI-UK-100007",
        "first_name": "Thomas",
        "last_name": "O'Brien",
        "date_of_birth": "1972-12-03",
        "postcode": "CF10 1EP",
        "email": "thomas.obrien@email.co.uk",
        "phone": "+44 7700 900007",
        "address": "3 Castle Street, Cardiff CF10 1EP",
        "account_opened": "2016-04-22",
        "account_type": "current",
        "risk_score": 7,
        "eligibility_flags": {"pre_approved": False, "existing_loan_holder": True, "premium_customer": False},
        "existing_credit_obligations": [
            {"type": "personal_loan", "provider": "Citibank", "balance": 15000, "monthly_payment": 420, "remaining_months": 36},
            {"type": "credit_card", "provider": "Citibank", "balance": 4800, "monthly_payment": 140, "limit": 6000},
            {"type": "credit_card", "provider": "HSBC", "balance": 2100, "monthly_payment": 65, "limit": 3000}
        ],
        "annual_income": 35000,
        "employment_status": "full_time",
        "residency_status": "uk_resident",
    },
    {
        "customer_id": "CITI-UK-100008",
        "first_name": "Amara",
        "last_name": "Okafor",
        "date_of_birth": "1993-08-27",
        "postcode": "BS1 5DB",
        "email": "amara.okafor@email.co.uk",
        "phone": "+44 7700 900008",
        "address": "90 Queen Charlotte Street, Bristol BS1 5DB",
        "account_opened": "2021-06-18",
        "account_type": "current",
        "risk_score": 4,
        "eligibility_flags": {"pre_approved": True, "existing_loan_holder": False, "premium_customer": False},
        "existing_credit_obligations": [],
        "annual_income": 48000,
        "employment_status": "full_time",
        "residency_status": "uk_visa",
    },
    {
        "customer_id": "CITI-UK-100009",
        "first_name": "George",
        "last_name": "Taylor",
        "date_of_birth": "1958-01-11",
        "postcode": "EH1 1RE",
        "email": "george.taylor@email.co.uk",
        "phone": "+44 7700 900009",
        "address": "14 Princes Street, Edinburgh EH1 1RE",
        "account_opened": "2010-02-28",
        "account_type": "both",
        "risk_score": 2,
        "eligibility_flags": {"pre_approved": True, "existing_loan_holder": False, "premium_customer": True},
        "existing_credit_obligations": [
            {"type": "mortgage", "provider": "Nationwide", "balance": 85000, "monthly_payment": 650, "remaining_months": 120}
        ],
        "annual_income": 72000,
        "employment_status": "full_time",
        "residency_status": "uk_resident",
    },
    {
        "customer_id": "CITI-UK-100010",
        "first_name": "Lucy",
        "last_name": "Nguyen",
        "date_of_birth": "2000-04-05",
        "postcode": "NE1 4ST",
        "email": "lucy.nguyen@email.co.uk",
        "phone": "+44 7700 900010",
        "address": "28 Grey Street, Newcastle NE1 4ST",
        "account_opened": "2023-09-01",
        "account_type": "savings",
        "risk_score": 6,
        "eligibility_flags": {"pre_approved": False, "existing_loan_holder": False, "premium_customer": False},
        "existing_credit_obligations": [
            {"type": "credit_card", "provider": "Monzo", "balance": 800, "monthly_payment": 25, "limit": 1500}
        ],
        "annual_income": 24000,
        "employment_status": "part_time",
        "residency_status": "uk_resident",
    },
]

LOAN_PRODUCTS = [
    {
        "product_code": "PERS_LOAN",
        "product_name": "Citi Personal Loan",
        "description": (
            "A flexible personal loan for any purpose — from a new car to a dream holiday. "
            "Borrow between £1,000 and £25,000 with fixed monthly repayments over 1 to 5 years. "
            "Enjoy competitive rates with no arrangement fees."
        ),
        "min_amount": 1000,
        "max_amount": 25000,
        "min_term_months": 12,
        "max_term_months": 60,
        "representative_apr": 9.9,
        "min_apr": 6.9,
        "max_apr": 29.9,
        "eligibility_criteria": {
            "min_age": 18,
            "max_age": 75,
            "min_income": 12000,
            "residency": ["uk_resident", "uk_visa"],
            "employment": ["full_time", "part_time", "self_employed", "retired"],
        },
        "early_repayment_fee_pct": 1.0,
        "early_repayment_details": (
            "You can repay your loan early at any time. An early repayment charge of up to "
            "58 days' interest may apply, equivalent to approximately 1% of the outstanding balance. "
            "No fee applies if you overpay by up to 10% of the balance per year."
        ),
        "features": [
            "No arrangement fee",
            "Fixed monthly repayments",
            "Borrow £1,000 to £25,000",
            "Repay over 1 to 5 years",
            "Check your rate without affecting your credit score",
        ],
        "fca_disclosure": (
            "Representative example: If you borrow £10,000 over 48 months at a fixed rate of "
            "9.9% p.a. (representative 9.9% APR), you would pay 48 monthly repayments of £248.85. "
            "Total amount payable: £11,944.80. The rate you are offered may differ based on your "
            "individual circumstances and credit history. 51% of successful applicants received "
            "the representative APR. Credit is subject to status and affordability checks."
        ),
    },
    {
        "product_code": "DEBT_CONSOL",
        "product_name": "Citi Debt Consolidation Loan",
        "description": (
            "Simplify your finances by combining existing debts into one manageable monthly payment. "
            "Borrow between £5,000 and £50,000 over 2 to 7 years. Lower your overall monthly "
            "outgoings and take control of your debt."
        ),
        "min_amount": 5000,
        "max_amount": 50000,
        "min_term_months": 24,
        "max_term_months": 84,
        "representative_apr": 7.9,
        "min_apr": 5.9,
        "max_apr": 19.9,
        "eligibility_criteria": {
            "min_age": 21,
            "max_age": 70,
            "min_income": 18000,
            "residency": ["uk_resident"],
            "employment": ["full_time", "part_time", "self_employed"],
            "min_existing_debt": 3000,
        },
        "early_repayment_fee_pct": 1.5,
        "early_repayment_details": (
            "You may repay your loan early at any time. An early settlement fee equivalent to "
            "up to 58 days' interest will apply (approximately 1.5% of the outstanding balance). "
            "Partial overpayments of up to 10% of the balance per year are fee-free."
        ),
        "features": [
            "One simple monthly payment",
            "Potentially lower total interest",
            "Borrow £5,000 to £50,000",
            "Repay over 2 to 7 years",
            "Free debt consolidation guidance",
            "No arrangement fee",
        ],
        "fca_disclosure": (
            "Representative example: If you borrow £20,000 over 60 months at a fixed rate of "
            "7.9% p.a. (representative 7.9% APR), you would pay 60 monthly repayments of £404.44. "
            "Total amount payable: £24,266.40. Your rate depends on your personal circumstances. "
            "49% of successful applicants received the representative APR. Consolidating debts "
            "may mean you pay more interest overall if you extend the repayment period. "
            "Credit is subject to status and affordability checks."
        ),
    },
    {
        "product_code": "HOME_IMPROV",
        "product_name": "Citi Home Improvement Loan",
        "description": (
            "Transform your home with a dedicated home improvement loan. Borrow between £7,500 "
            "and £50,000 over 1 to 10 years. Whether it's a new kitchen, loft conversion, or "
            "energy-efficient upgrades — we've got you covered with our lowest rates."
        ),
        "min_amount": 7500,
        "max_amount": 50000,
        "min_term_months": 12,
        "max_term_months": 120,
        "representative_apr": 6.9,
        "min_apr": 4.9,
        "max_apr": 14.9,
        "eligibility_criteria": {
            "min_age": 21,
            "max_age": 75,
            "min_income": 20000,
            "residency": ["uk_resident"],
            "employment": ["full_time", "part_time", "self_employed", "retired"],
            "homeowner_required": True,
        },
        "early_repayment_fee_pct": 0.5,
        "early_repayment_details": (
            "You can repay your loan early with minimal fees. An early repayment charge of up to "
            "28 days' interest may apply (approximately 0.5% of the outstanding balance). "
            "Overpayments of up to 20% of the balance per year are completely free."
        ),
        "features": [
            "Our lowest personal loan rates",
            "No arrangement fee",
            "Borrow £7,500 to £50,000",
            "Repay over 1 to 10 years",
            "Fixed monthly repayments",
            "Dedicated home improvement guidance",
        ],
        "fca_disclosure": (
            "Representative example: If you borrow £15,000 over 60 months at a fixed rate of "
            "6.9% p.a. (representative 6.9% APR), you would pay 60 monthly repayments of £296.69. "
            "Total amount payable: £17,801.40. The rate offered depends on your individual "
            "circumstances. 51% of successful applicants received the representative APR. "
            "This is an unsecured loan — your home is not at risk. "
            "Credit is subject to status and affordability checks."
        ),
    },
]

PREQUALIFICATION_RULES = [
    # Personal Loan rules
    {"product_code": "PERS_LOAN", "rule_name": "Income Multiplier", "rule_type": "income_multiplier",
     "parameters": {"multiplier": 4.0}, "priority": 1},
    {"product_code": "PERS_LOAN", "rule_name": "Max DTI Ratio", "rule_type": "dti_ratio",
     "parameters": {"max_ratio": 0.45}, "priority": 2},
    {"product_code": "PERS_LOAN", "rule_name": "Risk Score Threshold", "rule_type": "risk_score",
     "parameters": {"max_risk_score": 8}, "priority": 3},

    # Debt Consolidation rules
    {"product_code": "DEBT_CONSOL", "rule_name": "Income Multiplier", "rule_type": "income_multiplier",
     "parameters": {"multiplier": 5.0}, "priority": 1},
    {"product_code": "DEBT_CONSOL", "rule_name": "Max DTI Ratio", "rule_type": "dti_ratio",
     "parameters": {"max_ratio": 0.50}, "priority": 2},
    {"product_code": "DEBT_CONSOL", "rule_name": "Risk Score Threshold", "rule_type": "risk_score",
     "parameters": {"max_risk_score": 7}, "priority": 3},

    # Home Improvement rules
    {"product_code": "HOME_IMPROV", "rule_name": "Income Multiplier", "rule_type": "income_multiplier",
     "parameters": {"multiplier": 5.5}, "priority": 1},
    {"product_code": "HOME_IMPROV", "rule_name": "Max DTI Ratio", "rule_type": "dti_ratio",
     "parameters": {"max_ratio": 0.40}, "priority": 2},
    {"product_code": "HOME_IMPROV", "rule_name": "Risk Score Threshold", "rule_type": "risk_score",
     "parameters": {"max_risk_score": 6}, "priority": 3},
]

ADMIN_CONFIG = [
    {
        "config_key": "agent_greeting",
        "config_value": {"message": "Welcome to Citibank UK! I'm your Loan Application Assistant. How can I help you today?"},
        "description": "Default greeting message for the agent",
    },
    {
        "config_key": "fca_global_disclaimer",
        "config_value": {
            "text": (
                "Important: All loan quotes are indicative and subject to full credit and affordability assessment. "
                "Your home is not at risk with our unsecured personal loans. "
                "Citibank UK is authorised and regulated by the Financial Conduct Authority (FCA). "
                "We are committed to treating customers fairly in line with FCA Consumer Duty requirements."
            )
        },
        "description": "Global FCA disclaimer shown with pre-qualification results",
    },
    {
        "config_key": "max_prequalification_attempts",
        "config_value": {"value": 3},
        "description": "Maximum number of pre-qualification attempts per session",
    },
    {
        "config_key": "prequalification_enabled",
        "config_value": {"enabled": True},
        "description": "Toggle pre-qualification engine on/off",
    },
]


def create_database():
    """Create loan_agent database if it doesn't exist."""
    conn = psycopg2.connect(ADMIN_DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'loan_agent'")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE loan_agent")
        print("Created database: loan_agent")
    else:
        print("Database loan_agent already exists")
    cur.close()
    conn.close()


def seed():
    """Create schema and insert mock data."""
    create_database()

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Create schema
    cur.execute(SCHEMA_SQL)
    conn.commit()
    print("Schema created successfully")

    # Clear existing data
    cur.execute("TRUNCATE customers, loan_products, prequalification_rules, prequalification_results, admin_config RESTART IDENTITY CASCADE")
    conn.commit()

    # Insert customers
    for c in CUSTOMERS:
        cur.execute("""
            INSERT INTO customers (
                customer_id, first_name, last_name, date_of_birth, postcode,
                email, phone, address, account_opened, account_type,
                risk_score, eligibility_flags, existing_credit_obligations,
                annual_income, employment_status, residency_status
            ) VALUES (
                %(customer_id)s, %(first_name)s, %(last_name)s, %(date_of_birth)s, %(postcode)s,
                %(email)s, %(phone)s, %(address)s, %(account_opened)s, %(account_type)s,
                %(risk_score)s, %(eligibility_flags)s, %(existing_credit_obligations)s,
                %(annual_income)s, %(employment_status)s, %(residency_status)s
            )
        """, {
            **c,
            "eligibility_flags": json.dumps(c["eligibility_flags"]),
            "existing_credit_obligations": json.dumps(c["existing_credit_obligations"]),
        })
    print(f"Inserted {len(CUSTOMERS)} customers")

    # Insert loan products
    for p in LOAN_PRODUCTS:
        cur.execute("""
            INSERT INTO loan_products (
                product_code, product_name, description,
                min_amount, max_amount, min_term_months, max_term_months,
                representative_apr, min_apr, max_apr,
                eligibility_criteria, early_repayment_fee_pct, early_repayment_details,
                features, fca_disclosure
            ) VALUES (
                %(product_code)s, %(product_name)s, %(description)s,
                %(min_amount)s, %(max_amount)s, %(min_term_months)s, %(max_term_months)s,
                %(representative_apr)s, %(min_apr)s, %(max_apr)s,
                %(eligibility_criteria)s, %(early_repayment_fee_pct)s, %(early_repayment_details)s,
                %(features)s, %(fca_disclosure)s
            )
        """, {
            **p,
            "eligibility_criteria": json.dumps(p["eligibility_criteria"]),
            "features": json.dumps(p["features"]),
        })
    print(f"Inserted {len(LOAN_PRODUCTS)} loan products")

    # Insert pre-qualification rules
    for r in PREQUALIFICATION_RULES:
        cur.execute("""
            INSERT INTO prequalification_rules (
                product_code, rule_name, rule_type, parameters, priority
            ) VALUES (
                %(product_code)s, %(rule_name)s, %(rule_type)s, %(parameters)s, %(priority)s
            )
        """, {
            **r,
            "parameters": json.dumps(r["parameters"]),
        })
    print(f"Inserted {len(PREQUALIFICATION_RULES)} pre-qualification rules")

    # Insert admin config
    for cfg in ADMIN_CONFIG:
        cur.execute("""
            INSERT INTO admin_config (config_key, config_value, description)
            VALUES (%(config_key)s, %(config_value)s, %(description)s)
        """, {
            **cfg,
            "config_value": json.dumps(cfg["config_value"]),
        })
    print(f"Inserted {len(ADMIN_CONFIG)} admin config entries")

    conn.commit()
    cur.close()
    conn.close()
    print("\nSeed completed successfully!")
    print(f"Database: {DATABASE_URL}")


if __name__ == "__main__":
    seed()
