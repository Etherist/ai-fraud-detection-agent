"""Command Line Interface for AI Fraud Detection Agent."""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

from src.agents.document_ingestor import DocumentIngestor
from src.agents.data_extractor import DataExtractor
from src.agents.api_lookup_agent import APILookupAgent
from src.agents.anomaly_detector import AnomalyDetector
from src.agents.aml_checker import AMLChecker
from src.agents.risk_scorer import RiskScorer
from src.agents.report_generator import ReportGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='AI Fraud Detection Agent for SME Loans - CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --bank-statement data/sample_bank_statements.csv --tax-return data/sample_tax_returns.csv
  %(prog)s --bank-statement statement.pdf --tax-return tax.pdf --output my_report.pdf
  %(prog)s --bank-statement bank.csv --tax-return tax.csv --format markdown
        """
    )
    parser.add_argument(
        '--bank-statement',
        type=str,
        required=True,
        help='Path to bank statement file (CSV or PDF)'
    )
    parser.add_argument(
        '--tax-return',
        type=str,
        required=True,
        help='Path to tax return file (CSV or PDF)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='report.pdf',
        help='Output report filename (default: report.pdf)'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['pdf', 'markdown'],
        default='pdf',
        help='Report format (default: pdf)'
    )
    parser.add_argument(
        '--mock-api',
        action='store_true',
        help='Use mock ABR/ATO APIs (default: True for demo)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    return parser.parse_args()


def main():
    """Main CLI entry point."""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("=" * 60)
    print("🛡️  AI Fraud Detection Agent for SME Loans")
    print("   CLI Mode - APRA APS 222 Compliant")
    print("=" * 60)
    print()

    # Validate input files exist
    bank_path = Path(args.bank_statement)
    tax_path = Path(args.tax_return)

    if not bank_path.exists():
        logger.error(f"Bank statement file not found: {bank_path}")
        sys.exit(1)
    if not tax_path.exists():
        logger.error(f"Tax return file not found: {tax_path}")
        sys.exit(1)

    # Validate output path is within current working directory (prevent directory traversal)
    output_path = Path(args.output).resolve()
    cwd = Path.cwd().resolve()
    if not output_path.is_relative_to(cwd):
        logger.error(f"Output path {args.output} is outside current directory")
        sys.exit(1)

    print(f"📄 Bank Statement: {bank_path}")
    print(f"📄 Tax Return: {tax_path}")
    print(f"📊 Output: {args.output} ({args.format})")
    print()

    try:
        # Initialize agents
        print("🔧 Initializing agents...")
        ingestor = DocumentIngestor()
        extractor = DataExtractor()
        lookup_agent = APILookupAgent() if args.mock_api else None
        detector = AnomalyDetector()
        aml = AMLChecker()
        scorer = RiskScorer()
        reporter = ReportGenerator(output_dir=str(Path(args.output).parent))

        # Processing pipeline
        print("📥 Step 1: Ingesting documents...")
        bank_raw = ingestor.ingest_file(str(bank_path))
        tax_raw = ingestor.ingest_file(str(tax_path))
        print(f"   ✓ Bank statement: {bank_raw.get('row_count', 'N/A')} rows")
        print(f"   ✓ Tax return: {tax_raw.get('char_count', 'N/A')} chars")

        print("🔍 Step 2: Extracting data...")
        bank_data = extractor.extract(bank_raw)
        tax_data = extractor.extract(tax_raw)
        transactions = bank_data.get('transactions', [])
        business_details = {
            'business_name': tax_data.get('business_name', bank_data.get('business_name', 'Unknown')),
            'abn': tax_data.get('abn', bank_data.get('abn', '')),
            'addresses': tax_data.get('addresses', [])
        }
        print(f"   ✓ Extracted {len(transactions)} transactions")
        print(f"   ✓ Business: {business_details['business_name']} (ABN: {business_details['abn']})")

        if lookup_agent:
            print("🌐 Step 3: API lookups...")
            abn = business_details['abn']
            name = business_details['business_name']
            if abn and name:
                abr_result = lookup_agent.lookup_business(abn, name)
                print(f"   ✓ ABR: {abr_result['status']} (Valid: {abr_result['valid']})")
                ato_result = lookup_agent.lookup_tax_return(abn)
                print(f"   ✓ ATO: Tax return filed={ato_result['found']}")
            else:
                print("   ⚠️  Skipping API lookups (ABN/name missing)")

        print("📊 Step 4: Anomaly detection...")
        anomalies = detector.detect_anomalies(transactions)
        print(f"   ✓ Detected {len(anomalies)} anomalies")
        for a in anomalies:
            print(f"     · {a['type']}: ${a['amount']:,.2f} ({a['severity']})")

        print("🔎 Step 5: AML screening...")
        aml_alerts = aml.check_transactions(transactions, business_details)
        print(f"   ✓ {len(aml_alerts)} AML alerts found")
        for alert in aml_alerts:
            print(f"     · {alert['type']}: {alert['message']}")

        print("📈 Step 6: Risk scoring...")
        risk_data = scorer.calculate_score(anomalies, aml_alerts)
        print(f"   ✓ Risk Score: {risk_data['score']}/100 ({risk_data['category']})")
        print(f"   ✓ APRA Code: {risk_data['apra_fields']['regulatory_code']}")
        print(f"   ✓ Asset Classification: {risk_data['apra_fields']['asset_classification']}")
        print(f"   ✓ Impairment Provision: ${risk_data['apra_fields']['impairment_provision']:,.2f}")

        print(f"📄 Step 7: Generating {args.format} report...")
        report_path = reporter.generate_report(
            risk_data=risk_data,
            anomalies=anomalies,
            aml_alerts=aml_alerts,
            business_details=business_details,
            task_id=Path(args.output).stem,
            format=args.format
        )
        print(f"   ✓ Report saved: {report_path}")

        print()
        print("=" * 60)
        print("✅ Analysis Complete!")
        print(f"📊 Risk Score: {risk_data['score']}/100 ({risk_data['category']})")
        print(f"📄 Report: {report_path}")
        print("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
