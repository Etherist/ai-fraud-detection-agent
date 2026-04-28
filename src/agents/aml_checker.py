"""AML Checker Agent - Screens for AML risks (high-risk jurisdictions, watchlists)."""

import logging
from typing import List, Dict, Any, Set
from src.utils.helpers import load_json_file, validate_abn

logger = logging.getLogger(__name__)


class AMLChecker:
    """Agent that screens transactions and business details for AML risks."""

    def __init__(self, watchlist_path: str = None, shell_company_path: str = None):
        """
        Initialize AMLChecker.

        Args:
            watchlist_path: Path to AML watchlist JSON
            shell_company_path: Path to shell company indicators JSON
        """
        self.watchlist = load_json_file(watchlist_path or "data/aml_watchlist.json")
        self.shell_indicators = load_json_file(shell_company_path or "data/shell_company_addresses.json")

        # Flatten watchlist for fast lookup
        self.high_risk_jurisdictions: Set[str] = set(self.watchlist.get('jurisdictions', []))
        self.watchlist_entities: Set[str] = set(self.watchlist.get('entities', []))
        self.watchlist_abns: Set[str] = set(self.watchlist.get('abns', []))

        logger.info(
            f"AMLChecker initialized: {len(self.high_risk_jurisdictions)} jurisdictions, "
            f"{len(self.watchlist_entities)} entities, {len(self.watchlist_abns)} ABNs"
        )

    def check_transactions(self, transactions: List[Dict[str, Any]], business_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Screen transactions for AML risks.

        Args:
            transactions: List of transaction dictionaries
            business_details: Business details including abn, business_name, addresses

        Returns:
            List of AML alert dictionaries with keys:
                - type: Category of alert ("high_risk_jurisdiction", "watchlist_entity", "shell_company")
                - transaction_id: ID of transaction (if applicable)
                - severity: "high" or "medium"
                - message: Human-readable explanation
                - detail: Additional context
        """
        logger.info(f"Checking {len(transactions)} transactions for AML risks")

        alerts = []

        # Check each transaction
        for tx in transactions:
            tx_alerts = self._check_transaction(tx, business_details)
            alerts.extend(tx_alerts)

        # Check business details themselves
        business_alerts = self._check_business_details(business_details)
        alerts.extend(business_alerts)

        # Deduplicate alerts
        unique_alerts = self._deduplicate_alerts(alerts)

        logger.info(f"Generated {len(unique_alerts)} AML alerts")
        return unique_alerts

    def _check_transaction(self, transaction: Dict[str, Any], business_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check a single transaction for AML red flags."""
        alerts = []

        # Extract transaction fields
        jurisdiction = transaction.get('counterparty_jurisdiction', '').upper().strip()
        counterparty = transaction.get('counterparty', '').strip()
        amount = float(transaction.get('amount', 0))
        description = str(transaction.get('description', '')).lower()
        tx_id = transaction.get('transaction_id', 'N/A')

        # Check: High-risk jurisdiction
        if jurisdiction and jurisdiction in self.high_risk_jurisdictions:
            alerts.append({
                "type": "high_risk_jurisdiction",
                "transaction_id": tx_id,
                "severity": "high",
                "message": f"Transaction with high-risk jurisdiction: {jurisdiction}",
                "detail": f"Counterparty jurisdiction '{jurisdiction}' is on AML watchlist",
                "field": "jurisdiction",
                "value": jurisdiction
            })

        # Check: Watchlist entity match
        if counterparty and counterparty in self.watchlist_entities:
            alerts.append({
                "type": "watchlist_entity",
                "transaction_id": tx_id,
                "severity": "high",
                "message": f"Counterparty matches sanctions/watchlist: {counterparty}",
                "detail": f"Entity '{counterparty}' appears on AML watchlist",
                "field": "counterparty",
                "value": counterparty
            })

        # Check: Structuring (multiple transactions just under reporting threshold)
        # In Australia, reporting threshold is usually $10,000 for cash transactions
        if amount >= 9000 and amount < 10000:
            alerts.append({
                "type": "possible_structuring",
                "transaction_id": tx_id,
                "severity": "medium",
                "message": f"Transactionamount near reporting threshold: ${amount:,.2f}",
                "detail": "Multiple transactions just under $10k may indicate structuring",
                "field": "amount",
                "value": amount
            })

        # Check: Round-dollar with high-risk description
        if amount >= 10000 and amount % 10000 == 0:
            keywords = ['loan', 'transfer', 'payment', 'deposit']
            if any(kw in description for kw in keywords):
                alerts.append({
                    "type": "suspicious_pattern",
                    "transaction_id": tx_id,
                    "severity": "medium",
                    "message": f"Large round-dollar transaction with generic description",
                    "detail": f"Amount ${amount:,.2f} with description: '{description[:50]}...'",
                    "field": "description",
                    "value": description[:50]
                })

        return alerts

    def _check_business_details(self, business_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check business registration details for AML risks."""
        alerts = []

        abn = str(business_details.get('abn', '')).strip()
        business_name = str(business_details.get('business_name', '')).strip()
        addresses = business_details.get('addresses', [])

        # Normalize ABN to 11 digits (left-pad with zeros) for watchlist matching
        if abn:
            abn_normalized = abn.zfill(11)
        else:
            abn_normalized = ''

        # Check: ABN on watchlist
        if abn_normalized and abn_normalized in self.watchlist_abns:
            alerts.append({
                "type": "watchlist_abn",
                "transaction_id": None,
                "severity": "high",
                "message": f"Business ABN on sanctions list: {abn}",
                "detail": "This ABN is associated with a high-risk entity",
                "field": "abn",
                "value": abn
            })

        # Check: Business name on watchlist
        if business_name and business_name in self.watchlist_entities:
            alerts.append({
                "type": "watchlist_business_name",
                "transaction_id": None,
                "severity": "high",
                "message": f"Business name matches watchlist: {business_name}",
                "detail": "This business name appears on AML sanctions list",
                "field": "business_name",
                "value": business_name
            })

        # Check: Shell company indicators in address
        for address in addresses:
            if any(indicator.lower() in address.lower() for indicator in self.shell_indicators.get('shell_indicators', [])):
                alerts.append({
                    "type": "shell_company_indicator",
                    "transaction_id": None,
                    "severity": "medium",
                    "message": "Potential shell company address detected",
                    "detail": f"Address contains shell company indicator: {address}",
                    "field": "address",
                    "value": address
                })

        return alerts

    def _deduplicate_alerts(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate alerts based on type and transaction_id."""
        seen = set()
        unique = []

        for alert in alerts:
            key = (alert['type'], alert.get('transaction_id'), alert.get('value', ''))
            if key not in seen:
                seen.add(key)
                unique.append(alert)

        return unique


def check_aml(transactions: List[Dict[str, Any]], business_details: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convenience function for AML checking."""
    checker = AMLChecker()
    return checker.check_transactions(transactions, business_details)
