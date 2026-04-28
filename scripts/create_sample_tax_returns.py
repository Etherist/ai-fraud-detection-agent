"""Sample tax returns CSV for demo and testing."""

import csv
import os

def create_sample_tax_returns_csv():
    """Create a sample tax return CSV file."""
    csv_path = "data/sample_tax_returns.csv"
    os.makedirs("data", exist_ok=True)

    tax_data = {
        "business_name": "Acme Pty Ltd",
        "abn": "123456789",
        "acn": "123456789",
        "financial_year": "2025",
        "reported_revenue": 750000.00,
        "taxable_income": 520000.00,
        "tax_payable": 156000.00,
        "address": "123 Mock Street, Sydney NSW 2000, Australia",
        "entity_type": "Australian Proprietary Company",
        "tax_return_filed": True,
        "gst_registered": True,
        "gst_turnover": 750000.00
    }

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=tax_data.keys())
        writer.writeheader()
        writer.writerow(tax_data)

    print(f"✓ Created sample tax return at {csv_path}")

if __name__ == "__main__":
    create_sample_tax_returns_csv()
