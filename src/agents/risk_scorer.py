"""Risk Scorer Agent - Calculates composite risk score with APRA APS 222 alignment."""

import logging
from typing import List, Dict, Any
from src.utils.config import RISK_THRESHOLDS, IMPAIRMENT_RATES

logger = logging.getLogger(__name__)


class RiskScorer:
    """Agent that calculates risk scores based on anomalies and AML alerts with APRA APS 222 compliance."""

    # Point allocation rules (fixed thresholds for demo)
    # Points are assigned per anomaly/alert type+severity combination, no double-counting
    POINTS = {
        # Anomaly types
        "round_dollar": 20,
        "outlier_medium": 15,
        "outlier_high": 23,
        "high_value": 25,
        # AML alert types (by severity)
        "aml_high": 40,
        "aml_medium": 15,
        # Additional penalty for shell-related indicators (only if not already counted)
        "shell_company": 25,
    }

    def __init__(self, thresholds: Dict[str, int] = None):
        """
        Initialize RiskScorer.

        Args:
            thresholds: Risk category thresholds (e.g., {"Low": 30, "Medium": 70, "High": 100})
        """
        self.thresholds = thresholds or RISK_THRESHOLDS
        logger.info(f"RiskScorer initialized with thresholds: {self.thresholds}")

    def calculate_score(self, anomalies: List[Dict[str, Any]], aml_alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate composite risk score (0-100) and APRA-specific fields.

        Args:
            anomalies: List of anomaly dictionaries from AnomalyDetector
            aml_alerts: List of AML alert dictionaries from AMLChecker

        Returns:
            Dictionary with:
                - score: int (0-100)
                - category: "Low"/"Medium"/"High"
                - breakdown: Dict of point contributions
                - apra_fields: APRA APS 222-specific fields
        """
        logger.info(f"Calculating risk score from {len(anomalies)} anomalies, {len(aml_alerts)} AML alerts")

        breakdown = {
            "round_dollar_points": 0,
            "outlier_points": 0,
            "high_value_points": 0,
            "aml_points": 0,
            "shell_points": 0,
            "total_points": 0
        }

        # Calculate points from anomalies (clear mapping, no severity multiplier)
        total_points = 0

        for anomaly in anomalies:
            a_type = anomaly.get('type', '')
            severity = anomaly.get('severity', 'medium')

            if a_type == 'round_dollar':
                pts = self.POINTS['round_dollar']
                breakdown['round_dollar_points'] += pts
                total_points += pts

            elif a_type == 'outlier':
                # Outlier points depend on severity: medium=15, high=23
                if severity == 'high':
                    pts = self.POINTS['outlier_high']
                else:
                    pts = self.POINTS['outlier_medium']
                breakdown['outlier_points'] += pts
                total_points += pts

            elif a_type == 'high_value':
                pts = self.POINTS['high_value']
                breakdown['high_value_points'] += pts
                total_points += pts

        # Calculate points from AML alerts
        # Each alert gets points based on its type and severity.
        # Certain types (shell_company_indicator) get an extra penalty.
        aml_pts = 0
        shell_extra = 0  # Track shell penalty separately for breakdown
        for alert in aml_alerts:
            alert_type = alert.get('type', '')
            severity = alert.get('severity', 'medium')

            # High-risk jurisdiction, watchlist entity, watchlist business name → 40 pts
            if alert_type in ['high_risk_jurisdiction', 'watchlist_entity', 'watchlist_business_name']:
                pts = self.POINTS['aml_high']
            # Medium-severity alerts: structuring, suspicious_pattern → 15 pts
            elif severity == 'high':
                # Catch-all for any other high-severity alerts (e.g., watchlist_abn)
                pts = self.POINTS['aml_high']
            else:
                pts = self.POINTS['aml_medium']

            # Additional penalty for shell_company_indicator only (not double-count)
            if alert_type == 'shell_company_indicator':
                pts += self.POINTS['shell_company']
                shell_extra += self.POINTS['shell_company']

            aml_pts += pts

        breakdown['aml_points'] = aml_pts
        breakdown['shell_points'] = shell_extra
        total_points += aml_pts

        # Cap at 100
        score = min(total_points, 100)
        breakdown['total_points'] = total_points

        # Determine category
        if score < self.thresholds['Low']:
            category = "Low"
        elif score < self.thresholds['Medium']:
            category = "Medium"
        else:
            category = "High"

        # Calculate APRA-specific fields
        apra_fields = self._calculate_apra_fields(score, anomalies, aml_alerts)

        result = {
            "score": score,
            "category": category,
            "breakdown": breakdown,
            "apra_fields": apra_fields,
            "summary": {
                "total_anomalies": len(anomalies),
                "total_aml_alerts": len(aml_alerts)
            }
        }

        logger.info(f"Risk score: {score}/100 ({category})")
        return result

    def _calculate_apra_fields(self, score: int, anomalies: List[Dict[str, Any]], aml_alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate APRA APS 222-specific fields for compliance reporting.

        Args:
            score: Risk score (0-100)
            anomalies: List of detected anomalies
            aml_alerts: List of AML alerts

        Returns:
            Dictionary with APRA fields:
                - asset_classification: "Standard"/"Substandard"/"Doubtful"/"Loss"
                - impairment_provision: float (monetary amount)
                - regulatory_code: str (e.g., "APS222-001")
                - loan_to_value_ratio: float (0.0 to 1.0)
                - collateral_value: float
                - requires_review: bool
        """
        # Asset classification based on risk score (APRA APS 222 alignment)
        # Standard: 0-29, Substandard: 30-69, Doubtful: 70-89, Loss: 90-100
        if score >= 90:
            asset_class = "Loss"
        elif score >= 70:
            asset_class = "Doubtful"
        elif score >= 30:
            asset_class = "Substandard"
        else:
            asset_class = "Standard"

        # Calculate impairment provision (simplified for demo)
        # Calculate total suspicious amounts from anomalies
        suspicious_amount = sum(a.get('amount', 0) for a in anomalies if a.get('severity') == 'high')
        impairment_rate = IMPAIRMENT_RATES.get(asset_class, 0.0)
        impairment_provision = suspicious_amount * impairment_rate

        # Generate regulatory code
        code_map = {
            "Standard": "APS222-001",
            "Substandard": "APS222-002",
            "Doubtful": "APS222-003",
            "Loss": "APS222-004"
        }
        regulatory_code = code_map.get(asset_class, "APS222-001")

        # Calculate loan-to-value ratio (mock calculation)
        # In real implementation, this would use collateral valuation data
        total_exposure = sum(a.get('amount', 0) for a in anomalies if a.get('type') in ['high_value', 'outlier'])
        collateral_value = total_exposure * 0.5 if total_exposure > 0 else 1000000  # Mock 50% collateral
        ltv = min(total_exposure / collateral_value, 1.0) if collateral_value > 0 else 0.0

        # Determine if manual review required
        requires_review = score >= 50 or len(aml_alerts) > 0

        apra_fields = {
            "asset_classification": asset_class,
            "impairment_provision": round(impairment_provision, 2),
            "regulatory_code": regulatory_code,
            "collateral_value": round(collateral_value, 2),
            "loan_to_value_ratio": round(ltv, 4),
            "requires_manual_review": requires_review,
            "review_priority": "High" if score >= 70 else "Medium" if score >= 30 else "Low",
            "apra_reporting_category": self._get_apra_category(asset_class, aml_alerts)
        }

        logger.info(f"APRA fields: {apra_fields['asset_classification']}, Code: {regulatory_code}")
        return apra_fields

    @staticmethod
    def _get_apra_category(asset_class: str, aml_alerts: List[Dict[str, Any]]) -> str:
        """Determine APRA reporting category."""
        if any(a.get('severity') == 'high' for a in aml_alerts):
            return "CRITICAL_AML"
        elif asset_class in ["Doubtful", "Loss"]:
            return "HIGH_IMPAIRMENT"
        elif asset_class == "Substandard":
            return "ELEVATED_RISK"
        else:
            return "STANDARD"


def calculate_risk_score(anomalies: List[Dict[str, Any]], aml_alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function for risk scoring."""
    scorer = RiskScorer()
    return scorer.calculate_score(anomalies, aml_alerts)
