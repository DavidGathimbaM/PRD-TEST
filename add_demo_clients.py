from datetime import datetime
from database import get_db_connection, init_db


def add_client(cursor, client, accounts, liabilities):
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
        client["household_name"],

        client["client1_name"],
        client["client1_dob"],
        client["client1_age"],
        client["client1_ssn_last4"],

        client.get("client2_name"),
        client.get("client2_dob"),
        client.get("client2_age"),
        client.get("client2_ssn_last4"),

        client["monthly_inflow"],
        client["monthly_outflow"],
        client["private_reserve_balance"],
        client["investment_account_balance"],
        client["insurance_deductibles"],
        client["floor_amount"],

        client["trust_name"],
        client["trust_value"],

        now,
        now
    ))

    client_id = cursor.lastrowid

    for account in accounts:
        cursor.execute("""
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
        """, (
            client_id,
            account["owner"],
            account["category"],
            account["account_type"],
            account["account_name"],
            account["account_last4"],
            account["balance"],
            account["cash_balance"],
            account["as_of_date"]
        ))

    for liability in liabilities:
        cursor.execute("""
            INSERT INTO liabilities (
                client_id,
                liability_type,
                interest_rate,
                remaining_balance
            )
            VALUES (?, ?, ?, ?)
        """, (
            client_id,
            liability["liability_type"],
            liability["interest_rate"],
            liability["remaining_balance"]
        ))


def main():
    init_db()

    conn = get_db_connection()
    cursor = conn.cursor()

    existing_names = {
        row["household_name"]
        for row in cursor.execute("SELECT household_name FROM clients").fetchall()
    }

    demo_clients = [
        {
            "client": {
                "household_name": "Miller Family",
                "client1_name": "James Miller",
                "client1_dob": "02/18/1976",
                "client1_age": 49,
                "client1_ssn_last4": "2841",
                "client2_name": "Laura Miller",
                "client2_dob": "11/04/1978",
                "client2_age": 47,
                "client2_ssn_last4": "9135",
                "monthly_inflow": 18500,
                "monthly_outflow": 13200,
                "private_reserve_balance": 94000,
                "investment_account_balance": 26000,
                "insurance_deductibles": 4500,
                "floor_amount": 1000,
                "trust_name": "Miller Family Trust",
                "trust_value": 875000
            },
            "accounts": [
                {
                    "owner": "client1",
                    "category": "retirement",
                    "account_type": "401K",
                    "account_name": "James 401K",
                    "account_last4": "4412",
                    "balance": 318500,
                    "cash_balance": 3200,
                    "as_of_date": "06/28/2026"
                },
                {
                    "owner": "client1",
                    "category": "retirement",
                    "account_type": "Roth IRA",
                    "account_name": "James Roth IRA",
                    "account_last4": "9831",
                    "balance": 84200,
                    "cash_balance": 1200,
                    "as_of_date": "06/28/2026"
                },
                {
                    "owner": "client2",
                    "category": "retirement",
                    "account_type": "IRA",
                    "account_name": "Laura IRA",
                    "account_last4": "7754",
                    "balance": 226000,
                    "cash_balance": 4000,
                    "as_of_date": "06/28/2026"
                },
                {
                    "owner": "joint",
                    "category": "non_retirement",
                    "account_type": "Brokerage",
                    "account_name": "Joint Brokerage",
                    "account_last4": "6620",
                    "balance": 410000,
                    "cash_balance": 15000,
                    "as_of_date": "06/28/2026"
                },
                {
                    "owner": "joint",
                    "category": "non_retirement",
                    "account_type": "Checking",
                    "account_name": "Pinnacle Checking",
                    "account_last4": "2088",
                    "balance": 38500,
                    "cash_balance": 38500,
                    "as_of_date": "06/28/2026"
                }
            ],
            "liabilities": [
                {
                    "liability_type": "Primary Mortgage",
                    "interest_rate": "4.10%",
                    "remaining_balance": 365000
                },
                {
                    "liability_type": "Auto Loan",
                    "interest_rate": "5.80%",
                    "remaining_balance": 22500
                }
            ]
        },
        {
            "client": {
                "household_name": "Johnson Household",
                "client1_name": "Robert Johnson",
                "client1_dob": "07/09/1969",
                "client1_age": 56,
                "client1_ssn_last4": "7204",
                "client2_name": "Elaine Johnson",
                "client2_dob": "05/14/1971",
                "client2_age": 54,
                "client2_ssn_last4": "1198",
                "monthly_inflow": 22000,
                "monthly_outflow": 15000,
                "private_reserve_balance": 128000,
                "investment_account_balance": 42000,
                "insurance_deductibles": 7000,
                "floor_amount": 1000,
                "trust_name": "Johnson Revocable Trust",
                "trust_value": 1250000
            },
            "accounts": [
                {
                    "owner": "client1",
                    "category": "retirement",
                    "account_type": "IRA",
                    "account_name": "Robert Traditional IRA",
                    "account_last4": "9021",
                    "balance": 640000,
                    "cash_balance": 8500,
                    "as_of_date": "06/28/2026"
                },
                {
                    "owner": "client2",
                    "category": "retirement",
                    "account_type": "401K",
                    "account_name": "Elaine 401K",
                    "account_last4": "3015",
                    "balance": 455000,
                    "cash_balance": 6200,
                    "as_of_date": "06/28/2026"
                },
                {
                    "owner": "client2",
                    "category": "retirement",
                    "account_type": "Roth IRA",
                    "account_name": "Elaine Roth IRA",
                    "account_last4": "8752",
                    "balance": 112000,
                    "cash_balance": 2400,
                    "as_of_date": "06/28/2026"
                },
                {
                    "owner": "joint",
                    "category": "non_retirement",
                    "account_type": "Taxable Brokerage",
                    "account_name": "Schwab Taxable Brokerage",
                    "account_last4": "5571",
                    "balance": 720000,
                    "cash_balance": 21000,
                    "as_of_date": "06/28/2026"
                }
            ],
            "liabilities": [
                {
                    "liability_type": "Primary Mortgage",
                    "interest_rate": "3.25%",
                    "remaining_balance": 510000
                }
            ]
        },
        {
            "client": {
                "household_name": "Carter Family",
                "client1_name": "Michael Carter",
                "client1_dob": "12/02/1981",
                "client1_age": 44,
                "client1_ssn_last4": "6650",
                "client2_name": "Natalie Carter",
                "client2_dob": "08/21/1983",
                "client2_age": 42,
                "client2_ssn_last4": "4927",
                "monthly_inflow": 14500,
                "monthly_outflow": 9800,
                "private_reserve_balance": 61000,
                "investment_account_balance": 18000,
                "insurance_deductibles": 3500,
                "floor_amount": 1000,
                "trust_name": "Carter Family Trust",
                "trust_value": 690000
            },
            "accounts": [
                {
                    "owner": "client1",
                    "category": "retirement",
                    "account_type": "401K",
                    "account_name": "Michael 401K",
                    "account_last4": "1150",
                    "balance": 205000,
                    "cash_balance": 1800,
                    "as_of_date": "06/28/2026"
                },
                {
                    "owner": "client2",
                    "category": "retirement",
                    "account_type": "403B",
                    "account_name": "Natalie 403B",
                    "account_last4": "9020",
                    "balance": 174000,
                    "cash_balance": 2100,
                    "as_of_date": "06/28/2026"
                },
                {
                    "owner": "joint",
                    "category": "non_retirement",
                    "account_type": "Brokerage",
                    "account_name": "Joint Brokerage",
                    "account_last4": "7440",
                    "balance": 198000,
                    "cash_balance": 9000,
                    "as_of_date": "06/28/2026"
                },
                {
                    "owner": "joint",
                    "category": "non_retirement",
                    "account_type": "Savings",
                    "account_name": "Private Reserve",
                    "account_last4": "3821",
                    "balance": 61000,
                    "cash_balance": 61000,
                    "as_of_date": "06/28/2026"
                }
            ],
            "liabilities": [
                {
                    "liability_type": "Primary Mortgage",
                    "interest_rate": "4.75%",
                    "remaining_balance": 410000
                },
                {
                    "liability_type": "Student Loan",
                    "interest_rate": "6.20%",
                    "remaining_balance": 38000
                },
                {
                    "liability_type": "Auto Loan",
                    "interest_rate": "5.40%",
                    "remaining_balance": 19000
                }
            ]
        },
        {
            "client": {
                "household_name": "Davis Household",
                "client1_name": "Patricia Davis",
                "client1_dob": "03/30/1965",
                "client1_age": 61,
                "client1_ssn_last4": "3388",
                "client2_name": "",
                "client2_dob": "",
                "client2_age": None,
                "client2_ssn_last4": "",
                "monthly_inflow": 11800,
                "monthly_outflow": 7600,
                "private_reserve_balance": 85000,
                "investment_account_balance": 31000,
                "insurance_deductibles": 2500,
                "floor_amount": 1000,
                "trust_name": "Davis Living Trust",
                "trust_value": 540000
            },
            "accounts": [
                {
                    "owner": "client1",
                    "category": "retirement",
                    "account_type": "IRA",
                    "account_name": "Patricia IRA",
                    "account_last4": "4107",
                    "balance": 395000,
                    "cash_balance": 7200,
                    "as_of_date": "06/28/2026"
                },
                {
                    "owner": "client1",
                    "category": "retirement",
                    "account_type": "Roth IRA",
                    "account_name": "Patricia Roth IRA",
                    "account_last4": "2219",
                    "balance": 154000,
                    "cash_balance": 3000,
                    "as_of_date": "06/28/2026"
                },
                {
                    "owner": "client1",
                    "category": "non_retirement",
                    "account_type": "Brokerage",
                    "account_name": "Schwab Individual Brokerage",
                    "account_last4": "6070",
                    "balance": 275000,
                    "cash_balance": 11000,
                    "as_of_date": "06/28/2026"
                },
                {
                    "owner": "client1",
                    "category": "non_retirement",
                    "account_type": "Savings",
                    "account_name": "Private Reserve",
                    "account_last4": "9442",
                    "balance": 85000,
                    "cash_balance": 85000,
                    "as_of_date": "06/28/2026"
                }
            ],
            "liabilities": [
                {
                    "liability_type": "Home Equity Line",
                    "interest_rate": "7.25%",
                    "remaining_balance": 62000
                }
            ]
        }
    ]

    added = 0

    for item in demo_clients:
        household_name = item["client"]["household_name"]

        if household_name in existing_names:
            print(f"Skipped existing client: {household_name}")
            continue

        add_client(
            cursor,
            item["client"],
            item["accounts"],
            item["liabilities"]
        )
        added += 1
        print(f"Added client: {household_name}")

    conn.commit()
    conn.close()

    print(f"Done. Added {added} new demo clients.")


if __name__ == "__main__":
    main()