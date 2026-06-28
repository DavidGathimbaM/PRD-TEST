import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.getenv(
    "RAILWAY_DATABASE_PATH",
    os.path.join(BASE_DIR, "instance", "app.db")
)


def get_db_connection():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            household_name TEXT NOT NULL,

            client1_name TEXT NOT NULL,
            client1_dob TEXT,
            client1_age INTEGER,
            client1_ssn_last4 TEXT,

            client2_name TEXT,
            client2_dob TEXT,
            client2_age INTEGER,
            client2_ssn_last4 TEXT,

            monthly_inflow REAL DEFAULT 0,
            monthly_outflow REAL DEFAULT 0,
            private_reserve_balance REAL DEFAULT 0,
            investment_account_balance REAL DEFAULT 0,
            insurance_deductibles REAL DEFAULT 0,
            floor_amount REAL DEFAULT 1000,

            trust_name TEXT,
            trust_value REAL DEFAULT 0,

            created_at TEXT,
            updated_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,

            owner TEXT NOT NULL,
            category TEXT NOT NULL,
            account_type TEXT NOT NULL,
            account_name TEXT,
            account_last4 TEXT,

            balance REAL DEFAULT 0,
            cash_balance REAL DEFAULT 0,
            as_of_date TEXT,

            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS liabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,

            liability_type TEXT NOT NULL,
            interest_rate TEXT,
            remaining_balance REAL DEFAULT 0,

            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,

            report_date TEXT,
            inflow REAL DEFAULT 0,
            outflow REAL DEFAULT 0,
            automated_transfer REAL DEFAULT 0,
            private_reserve_target REAL DEFAULT 0,

            client1_retirement_total REAL DEFAULT 0,
            client2_retirement_total REAL DEFAULT 0,
            non_retirement_total REAL DEFAULT 0,
            trust_value REAL DEFAULT 0,
            grand_total_net_worth REAL DEFAULT 0,
            liabilities_total REAL DEFAULT 0,

            created_at TEXT,

            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    """)

    conn.commit()
    conn.close()


def seed_database_if_empty():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS count FROM clients")
    count = cursor.fetchone()["count"]

    if count > 0:
        conn.close()
        return

    now = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO clients (
            household_name,

            client1_name,
            client1_dob,
            client1_age,
            client1_ssn_last4,

            client2_name,
            client2_dob,
            client2_age,
            client2_ssn_last4,

            monthly_inflow,
            monthly_outflow,
            private_reserve_balance,
            investment_account_balance,
            insurance_deductibles,
            floor_amount,

            trust_name,
            trust_value,

            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Sample Client Family",

        "Client 1",
        "01/15/1973",
        50,
        "1234",

        "Client 2",
        "03/22/1975",
        48,
        "5678",

        15000,
        12000,
        75000,
        15000,
        3000,
        1000,

        "Client 1 and Client 2 Family Trust",
        120000,

        now,
        now
    ))

    client_id = cursor.lastrowid

    accounts = [
        (
            client_id,
            "client1",
            "retirement",
            "Roth IRA",
            "Client 1 Roth IRA",
            "1118",
            11162.47,
            518,
            "07/25/2023"
        ),
        (
            client_id,
            "client1",
            "retirement",
            "IRA",
            "Client 1 IRA",
            "2222",
            0,
            0,
            "07/25/2023"
        ),
        (
            client_id,
            "client2",
            "retirement",
            "IRA",
            "Client 2 IRA",
            "3333",
            37232.48,
            876,
            "07/25/2023"
        ),
        (
            client_id,
            "client2",
            "retirement",
            "401K",
            "Client 2 401K",
            "4444",
            70042.00,
            0,
            "04/01/2023"
        ),
        (
            client_id,
            "joint",
            "non_retirement",
            "Checking",
            "Wells Fargo Main Checking",
            "5555",
            46310.00,
            0,
            "07/25/2023"
        ),
        (
            client_id,
            "joint",
            "non_retirement",
            "Brokerage",
            "Schwab Joint Brokerage",
            "6666",
            142998.04,
            0,
            "07/25/2023"
        )
    ]

    cursor.executemany("""
        INSERT INTO accounts (
            client_id,
            owner,
            category,
            account_type,
            account_name,
            account_last4,
            balance,
            cash_balance,
            as_of_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, accounts)

    liabilities = [
        (
            client_id,
            "Primary Mortgage",
            "3.50%",
            280000
        ),
        (
            client_id,
            "Auto Loan",
            "5.20%",
            16500
        )
    ]

    cursor.executemany("""
        INSERT INTO liabilities (
            client_id,
            liability_type,
            interest_rate,
            remaining_balance
        )
        VALUES (?, ?, ?, ?)
    """, liabilities)

    conn.commit()
    conn.close()


def get_all_clients():
    conn = get_db_connection()
    clients = conn.execute("""
        SELECT
            id,
            household_name,
            client1_name,
            client2_name,
            monthly_inflow,
            monthly_outflow,
            updated_at
        FROM clients
        ORDER BY household_name ASC
    """).fetchall()
    conn.close()

    return [dict(row) for row in clients]


def get_client_detail(client_id):
    conn = get_db_connection()

    client = conn.execute("""
        SELECT *
        FROM clients
        WHERE id = ?
    """, (client_id,)).fetchone()

    if client is None:
        conn.close()
        return None

    accounts = conn.execute("""
        SELECT *
        FROM accounts
        WHERE client_id = ?
        ORDER BY category ASC, owner ASC, account_type ASC
    """, (client_id,)).fetchall()

    liabilities = conn.execute("""
        SELECT *
        FROM liabilities
        WHERE client_id = ?
        ORDER BY liability_type ASC
    """, (client_id,)).fetchall()

    reports = conn.execute("""
        SELECT *
        FROM reports
        WHERE client_id = ?
        ORDER BY created_at DESC
        LIMIT 5
    """, (client_id,)).fetchall()

    conn.close()

    return {
        "client": dict(client),
        "accounts": [dict(row) for row in accounts],
        "liabilities": [dict(row) for row in liabilities],
        "reports": [dict(row) for row in reports]
    }


def create_client(client_data):
    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO clients (
            household_name,

            client1_name,
            client1_dob,
            client1_age,
            client1_ssn_last4,

            client2_name,
            client2_dob,
            client2_age,
            client2_ssn_last4,

            monthly_inflow,
            monthly_outflow,
            private_reserve_balance,
            investment_account_balance,
            insurance_deductibles,
            floor_amount,

            trust_name,
            trust_value,

            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        client_data.get("householdName", "").strip(),

        client_data.get("client1Name", "").strip(),
        client_data.get("client1Dob", "").strip(),
        client_data.get("client1Age") or None,
        client_data.get("client1SsnLast4", "").strip(),

        client_data.get("client2Name", "").strip(),
        client_data.get("client2Dob", "").strip(),
        client_data.get("client2Age") or None,
        client_data.get("client2SsnLast4", "").strip(),

        client_data.get("monthlyInflow", 0),
        client_data.get("monthlyOutflow", 0),
        client_data.get("privateReserveBalance", 0),
        client_data.get("investmentAccountBalance", 0),
        client_data.get("insuranceDeductibles", 0),
        client_data.get("floorAmount", 1000),

        client_data.get("trustName", "").strip(),
        client_data.get("trustValue", 0),

        now,
        now
    ))

    client_id = cursor.lastrowid

    starter_accounts = [
        (
            client_id,
            "client1",
            "retirement",
            "IRA",
            "Client 1 IRA",
            "",
            0,
            0,
            ""
        ),
        (
            client_id,
            "client2",
            "retirement",
            "IRA",
            "Client 2 IRA",
            "",
            0,
            0,
            ""
        ),
        (
            client_id,
            "joint",
            "non_retirement",
            "Brokerage",
            "Joint Brokerage",
            "",
            0,
            0,
            ""
        ),
        (
            client_id,
            "joint",
            "non_retirement",
            "Checking",
            "Primary Checking",
            "",
            0,
            0,
            ""
        )
    ]

    cursor.executemany("""
        INSERT INTO accounts (
            client_id,
            owner,
            category,
            account_type,
            account_name,
            account_last4,
            balance,
            cash_balance,
            as_of_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, starter_accounts)

    conn.commit()
    conn.close()

    return client_id


def save_report_history(client_id, report_data):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO reports (
            client_id,
            report_date,
            inflow,
            outflow,
            automated_transfer,
            private_reserve_target,
            client1_retirement_total,
            client2_retirement_total,
            non_retirement_total,
            trust_value,
            grand_total_net_worth,
            liabilities_total,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        client_id,
        report_data.get("reportDate"),
        report_data.get("inflow", 0),
        report_data.get("outflow", 0),
        report_data.get("automatedTransfer", 0),
        report_data.get("privateReserveTarget", 0),
        report_data.get("client1RetirementTotal", 0),
        report_data.get("client2RetirementTotal", 0),
        report_data.get("nonRetirementTotal", 0),
        report_data.get("trustValue", 0),
        report_data.get("grandTotalNetWorth", 0),
        report_data.get("liabilitiesTotal", 0),
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()