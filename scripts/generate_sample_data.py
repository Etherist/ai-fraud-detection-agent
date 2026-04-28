"""Generate sample data for demo and testing."""

import json
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

def generate_bank_statements(output_path: str = "data/sample_bank_statements.csv", num_transactions: int = 10):
    """Generate synthetic bank statement with fraud patterns."""
    data_dir = Path(output_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)

    # Business info
    businesses = [
        {"name": "Acme Pty Ltd", "abn": "123456789"},
        {"name": "Shell Corp", "abn": "999999999"},
        {"name": "Fake Biz", "abn": "888888888"},
        {"name": "Cash Business", "abn": "777777777"},
        {"name": "Offshore Co", "abn": "666666666"}
    ]

    jurisdictions = ["AU", "AU", "AU", "AU", "AU", "XY", "ZW"]  # More AU for realism

    transactions = []
    base_date = datetime(2025, 7, 1)

    for i in range(num_transactions):
        business = random.choice(businesses)
        jdx = random.choice(jurisdictions)

        # Transaction patterns
        if i == 2:  # Round-dollar to shell company (AML flag)
            amount = 10000.00
            description = "Round-dollar transfer to related party"
            counterparty = "Shell Corp"
        elif i == 4:  # Very large outlier
            amount = 250000.00
            description = "Loan Repayment - Principal"
            counterparty = "Fake Biz"
        elif i == 6:  # Unusual cash deposit
            amount = 15000.00
            description = "Large cash deposit"
            counterparty = "Cash Business"
        elif i == 9:  # High-risk jurisdiction
            amount = 30000.00
            description = "International transfer"
            counterparty = "Offshore Co"
            jdx = "ZW"
        else:
            # Normal transactions
            amounts = [50000.0, 12345.67, 750.50, 5000.0, 8000.0, 45000.0]
            amount = random.choice(amounts)
            description = random.choice([
                "Invoice Payment",
                "Supplier Payment",
                "Office Supplies",
                "Monthly Rent",
                "Equipment Purchase",
                "Client Payment"
            ])
            counterparty = business["name"]

        tx = {
            "transaction_id": i + 1,
            "date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "amount": round(amount, 2),
            "description": description,
            "business_name": business["name"],
            "abn": business["abn"],
            "counterparty": counterparty,
            "counterparty_jurisdiction": jdx
        }
        transactions.append(tx)

    # Write CSV
    fieldnames = ["transaction_id", "date", "amount", "description",
                  "business_name", "abn", "counterparty", "counterparty_jurisdiction"]

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)

    print(f"✓ Generated {num_transactions} transactions → {output_path}")

def generate_tax_return(output_path: str = "data/sample_tax_returns.csv"):
    """Generate synthetic tax return CSV."""
    data_dir = Path(output_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)

    tax_data = {
        "business_name": "Acme Pty Ltd",
        "abn": "123456789",
        "financial_year": "2025",
        "reported_revenue": 750000.00,
        "taxable_income": 520000.00,
        "address": "123 Mock Street, Sydney NSW 2000",
        "entity_type": "Australian Proprietary Company",
        "tax_return_filed": True
    }

    # Single-row CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=tax_data.keys())
        writer.writeheader()
        writer.writerow(tax_data)

    print(f"✓ Generated tax return → {output_path}")

def generate_aml_watchlist(output_path: str = "data/aml_watchlist.json"):
    """Generate AML watchlist with mock high-risk entities."""
    data_dir = Path(output_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)

    watchlist = {
        "jurisdictions": ["XY", "ZW", "KP", "AF", "IQ", "SD", "IR", "SY"],
        "entities": [
            "Shell Corp",
            "Fake Biz",
            "Phantom Ltd",
            "Cash Business",
            "Offshore Co",
            "Money Service Business"
        ],
        "abns": ["99999999999", "88888888888", "77777777777", "66666666666"],
        "sanctioned_countries": ["XY", "ZW", "KP", "IR", "SY"],
        "high_risk_business_types": [
            "Money Service Business",
            "Casino",
            "Precious Metals Dealer",
            "Cryptocurrency Exchange"
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(watchlist, f, indent=2)

    print(f"✓ Generated AML watchlist → {output_path}")

def generate_shell_company_indicators(output_path: str = "data/shell_company_addresses.json"):
    """Generate shell company indicator patterns."""
    data_dir = Path(output_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)

    indicators = {
        "shell_indicators": [
            "PO Box",
            "Virtual Office",
            "Registered Agent",
            "Nominee Shareholder",
            "Bearer Shares",
            "No Physical Presence",
            "Mail Forwarding",
            "C/O",
            "Care Of"
        ],
        "shell_addresses": [
            "Level 1, 123 Corporate St, Sydney NSW 2000",
            "PO Box 123, Melbourne VIC 3000",
            "Suite 456, Virtual Office Park, Brisbane QLD 4000"
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(indicators, f, indent=2)

    print(f"✓ Generated shell company indicators → {output_path}")

if __name__ == "__main__":
    print("Generating sample data for AI Fraud Detection Agent...")
    print("=" * 60)

    generate_bank_statements()
    generate_tax_return()
    generate_aml_watchlist()
    generate_shell_company_indicators()

    print("=" * 60)
    print("✅ All sample data generated!")
    print("\nFiles created:")
    print("  • data/sample_bank_statements.csv")
    print("  • data/sample_tax_returns.csv")
    print("  • data/aml_watchlist.json")
    print("  • data/shell_company_addresses.json")
