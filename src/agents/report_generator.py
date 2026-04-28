"""Report Generator Agent - Generates audit-ready PDF/Markdown reports with APRA-specific fields."""

import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from jinja2 import Template
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import io

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Agent that compiles findings into audit-ready reports with APRA-specific fields."""

    def __init__(self, output_dir: str = "reports/"):
        """
        Initialize ReportGenerator.

        Args:
            output_dir: Directory to save generated reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ReportGenerator initialized - output_dir: {self.output_dir}")

    def generate_report(
        self,
        risk_data: Dict[str, Any],
        anomalies: List[Dict[str, Any]],
        aml_alerts: List[Dict[str, Any]],
        business_details: Dict[str, Any],
        task_id: str,
        format: str = "pdf"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive fraud detection report.

        Args:
            risk_data: Output from RiskScorer
            anomalies: List of detected anomalies
            aml_alerts: List of AML alerts
            business_details: Business information
            task_id: Unique task identifier
            format: Output format ("pdf" or "markdown")

        Returns:
            Dictionary with report metadata:
                - report_path: str (absolute path)
                - report_url: str (relative URL for API)
                - format: str
                - generated_at: str
        """
        logger.info(f"Generating {format} report for task {task_id}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_{task_id}_{timestamp}.{format}"
        filepath = self.output_dir / filename

        if format.lower() == "pdf":
            self._generate_pdf_report(risk_data, anomalies, aml_alerts, business_details, filepath)
        elif format.lower() == "markdown":
            self._generate_markdown_report(risk_data, anomalies, aml_alerts, business_details, filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")

        report_url = f"/reports/audit_{task_id}_{timestamp}.{format}"

        logger.info(f"Report generated: {filepath}")

        return {
            "report_path": str(filepath.absolute()),
            "report_url": report_url,
            "format": format,
            "generated_at": timestamp,
            "filename": filename
        }

    def _generate_pdf_report(
        self,
        risk_data: Dict[str, Any],
        anomalies: List[Dict[str, Any]],
        aml_alerts: List[Dict[str, Any]],
        business_details: Dict[str, Any],
        filepath: Path
    ) -> None:
        """Generate PDF report using ReportLab."""

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        ))
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=12,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2E4057')
        ))
        styles.add(ParagraphStyle(
            name='AlertHigh',
            parent=styles['Normal'],
            textColor=colors.red,
            backColor=colors.HexColor('#FFE6E6'),
            borderPadding=5
        ))
        styles.add(ParagraphStyle(
            name='AlertMedium',
            parent=styles['Normal'],
            textColor=colors.orange,
            backColor=colors.HexColor('#FFF3E0'),
            borderPadding=5
        ))

        story = []

        # Title
        story.append(Paragraph("SME Loan Fraud & AML Detection Report", styles['CustomTitle']))
        story.append(Spacer(1, 12))

        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['SectionHeader']))
        summary_data = [
            ["Risk Score", f"{risk_data['score']}/100 ({risk_data['category']})"],
            ["Business Name", business_details.get('business_name', 'N/A')],
            ["ABN", business_details.get('abn', 'N/A')],
            ["Generated", datetime.now().strftime("%Y-%m-%d %H:%M")],
            ["Total Anomalies", str(len(anomalies))],
            ["AML Alerts", str(len(aml_alerts))]
        ]
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F1F5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))

        # APRA APS 222 Fields
        story.append(Paragraph("APRA APS 222 Compliance Fields", styles['SectionHeader']))
        apra_fields = risk_data.get('apra_fields', {})
        apra_data = [
            ["Asset Classification", apra_fields.get('asset_classification', 'N/A')],
            ["Impairment Provision", f"${apra_fields.get('impairment_provision', 0):,.2f}"],
            ["Regulatory Code", apra_fields.get('regulatory_code', 'N/A')],
            ["Loan-to-Value Ratio", f"{apra_fields.get('loan_to_value_ratio', 0):.2%}"],
            ["Collateral Value", f"${apra_fields.get('collateral_value', 0):,.2f}"],
            ["Manual Review Required", "Yes" if apra_fields.get('requires_manual_review') else "No"],
            ["Review Priority", apra_fields.get('review_priority', 'N/A')]
        ]
        apra_table = Table(apra_data, colWidths=[2*inch, 4*inch])
        apra_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FFECB3')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(apra_table)
        story.append(Spacer(1, 20))

        # Detected Anomalies
        if anomalies:
            story.append(Paragraph("Detected Anomalies", styles['SectionHeader']))
            anomaly_data = [["Type", "Transaction ID", "Amount", "Severity", "Message"]]
            for a in anomalies:
                anomaly_data.append([
                    a.get('type', 'N/A'),
                    str(a.get('transaction_id', 'N/A')),
                    f"${a.get('amount', 0):,.2f}",
                    a.get('severity', 'N/A'),
                    a.get('message', '')[:60]
                ])

            anomaly_table = Table(anomaly_data, colWidths=[1*inch, 1*inch, 1.2*inch, 1*inch, 2.3*inch])
            anomaly_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90A4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(anomaly_table)
            story.append(Spacer(1, 20))

        # AML Alerts
        if aml_alerts:
            story.append(Paragraph("AML Alerts (AUSTRAC)", styles['SectionHeader']))
            aml_data = [["Type", "Severity", "Transaction ID", "Message"]]
            for alert in aml_alerts:
                severity_style = "AlertHigh" if alert.get('severity') == 'high' else "AlertMedium"
                aml_data.append([
                    alert.get('type', 'N/A'),
                    alert.get('severity', 'N/A'),
                    str(alert.get('transaction_id', 'N/A')),
                    alert.get('message', '')[:60]
                ])

            aml_table = Table(aml_data, colWidths=[1.5*inch, 1*inch, 1*inch, 3*inch])
            aml_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D32F2F')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(aml_table)
            story.append(Spacer(1, 20))

        # Risk Score Visualization
        self._add_risk_gauge(story, risk_data['score'], styles)

        # Footer disclaimer
        story.append(Spacer(1, 30))
        disclaimer = Paragraph(
            "This is a demo report for educational purposes. "
            "Not intended for actual lending decisions. "
            "APRA APS 222 compliance is illustrative only.",
            styles['Italic']
        )
        story.append(disclaimer)

        # Build PDF
        doc.build(story)
        logger.info(f"PDF report saved: {filepath}")

    def _generate_markdown_report(
        self,
        risk_data: Dict[str, Any],
        anomalies: List[Dict[str, Any]],
        aml_alerts: List[Dict[str, Any]],
        business_details: Dict[str, Any],
        filepath: Path
    ) -> None:
        """Generate Markdown report using Jinja2 template."""
        template_str = """# SME Loan Fraud Detection Report

## Executive Summary

| Field | Value |
|-------|-------|
| Business Name | {{ business_details.business_name }} |
| ABN | {{ business_details.abn }} |
| Risk Score | **{{ risk_data.score }}/100 ({{ risk_data.category }})** |
| Generated | {{ timestamp }} |
| Total Anomalies | {{ anomalies|length }} |
| AML Alerts | {{ aml_alerts|length }} |

## APRA APS 222 Compliance Fields

| Field | Value |
|-------|-------|
| Asset Classification | {{ risk_data.apra_fields.asset_classification }} |
| Impairment Provision | ${{ "{:,.2f}".format(risk_data.apra_fields.impairment_provision) }} |
| Regulatory Code | {{ risk_data.apra_fields.regulatory_code }} |
| Loan-to-Value Ratio | {{ "%.2f%%"|format(risk_data.apra_fields.loan_to_value_ratio * 100) }} |
| Collateral Value | ${{ "{:,.2f}".format(risk_data.apra_fields.collateral_value) }} |
| Manual Review Required | {{ "Yes" if risk_data.apra_fields.requires_manual_review else "No" }} |
| Review Priority | {{ risk_data.apra_fields.review_priority }} |

## Detected Anomalies

{% if anomalies %}
| # | Type | Transaction ID | Amount | Severity | Message |
|---|------|---------------|--------|----------|---------|
{% for a in anomalies %}
| {{ loop.index }} | {{ a.type }} | {{ a.transaction_id }} | ${{ "{:,.2f}".format(a.amount) }} | {{ a.severity }} | {{ a.message }} |
{% endfor %}
{% else %}
No anomalies detected.
{% endif %}

## AML Alerts (AUSTRAC)

{% if aml_alerts %}
| # | Type | Severity | Transaction ID | Message |
|---|------|----------|---------------|---------|
{% for alert in aml_alerts %}
| {{ loop.index }} | {{ alert.type }} | {{ alert.severity }} | {{ alert.transaction_id or 'N/A' }} | {{ alert.message }} |
{% endfor %}
{% else %}
No AML alerts detected.
{% endif %}

## Risk Score Breakdown

- Round-dollar Transactions: {{ risk_data.breakdown.round_dollar_points }} points
- Outlier Transactions: {{ risk_data.breakdown.outlier_points }} points
- High-Value Transactions: {{ risk_data.breakdown.high_value_points }} points
- AML Risk: {{ risk_data.breakdown.aml_points }} points
- **Total: {{ risk_data.breakdown.total_points }}/100**

---
*Report ID: {{ task_id }} | Generated: {{ generated_at }}*
*This is a demo report for educational purposes.*
"""
        template = Template(template_str)
        html_content = template.render(
            business_details=business_details,
            risk_data=risk_data,
            anomalies=anomalies,
            aml_alerts=aml_alerts,
            task_id=filepath.stem,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        with open(filepath, 'w') as f:
            f.write(html_content)

        logger.info(f"Markdown report saved: {filepath}")

    def _add_risk_gauge(self, story, score: int, styles) -> None:
        """Add visual risk gauge to PDF report."""
        # Create a simple gauge chart using matplotlib
        fig, ax = plt.subplots(figsize=(6, 2))

        # Draw gauge background
        ax.barh([0], [100], height=0.5, color='lightgray', alpha=0.5)
        ax.barh([0], [score], height=0.5, color=self._get_risk_color(score))

        ax.set_xlim(0, 100)
        ax.set_ylim(-0.5, 0.5)
        ax.set_xlabel("Risk Score")
        ax.set_yticks([])
        ax.text(score, 0, f" {score}", va='center', fontweight='bold', fontsize=12)

        # Save to bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close(fig)
        buf.seek(0)

        # Add to story
        img = Image(buf, width=6*inch, height=1.5*inch)
        story.append(Paragraph("Risk Score Visualization", styles['SectionHeader']))
        story.append(img)
        story.append(Spacer(1, 12))

    @staticmethod
    def _get_risk_color(score: int) -> str:
        """Get color based on risk score."""
        if score < 30:
            return '#4CAF50'  # Green
        elif score < 70:
            return '#FF9800'  # Orange
        else:
            return '#F44336'  # Red


def generate_pdf_report(
    risk_data: Dict[str, Any],
    anomalies: List[Dict[str, Any]],
    aml_alerts: List[Dict[str, Any]],
    business_details: Dict[str, Any],
    output_path: str
) -> str:
    """
    Convenience function to generate a PDF report.

    Args:
        risk_data: Output from RiskScorer
        anomalies: List of anomalies
        aml_alerts: List of AML alerts
        business_details: Business information
        output_path: Path to save PDF

    Returns:
        Path to generated report
    """
    generator = ReportGenerator(output_dir=str(Path(output_path).parent))
    task_id = Path(output_path).stem.replace("audit_", "")
    result = generator.generate_report(
        risk_data=risk_data,
        anomalies=anomalies,
        aml_alerts=aml_alerts,
        business_details=business_details,
        task_id=task_id,
        format="pdf"
    )
    return result['report_path']
