"""Anomaly Detector Agent - Flags numerical anomalies using PyOD Isolation Forest."""

import logging
from typing import List, Dict, Any
import numpy as np
from pyod.models.iforest import IForest

from src.utils.config import ROUND_DOLLAR_THRESHOLD, OUTLIER_AMOUNT_THRESHOLD

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Agent that detects fraud-related anomalies in transaction data using PyOD Isolation Forest.

    Detection methods:
    1. Isolation Forest – statistical outlier detection on transaction amounts
    2. Round-dollar rule – flags transactions divisible by $1000 (potential structuring)
    3. High-value rule – flags single transactions exceeding threshold

    All rules are independent; a transaction may trigger multiple flags.
    """

    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        """
        Initialize AnomalyDetector.

        Args:
            contamination: Expected proportion of anomalies in dataset (0.0-0.5).
                           Higher values increase anomaly sensitivity.
            random_state: Random seed for reproducible model training.
        """
        self.contamination = contamination
        self.random_state = random_state
        self.model = None
        logger.info(f"AnomalyDetector initialized (contamination={contamination}, round_threshold=${ROUND_DOLLAR_THRESHOLD:,.0f})")

    def detect_anomalies(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect anomalies in transaction data.

        Args:
            transactions: List of transaction dictionaries with keys:
                - transaction_id: unique identifier (any hashable)
                - amount: transaction amount (float, >0)
                - date: transaction date (string, any format)
                - description: optional transaction description

        Returns:
            List of anomaly dictionaries, each containing:
                - type: "outlier" | "round_dollar" | "high_value"
                - transaction_id: original transaction identifier
                - amount: transaction amount
                - severity: "high" | "medium" (risk level)
                - message: Human-readable explanation
        """
        logger.info(f"Detecting anomalies in {len(transactions)} transactions")

        if not transactions:
            logger.warning("No transactions provided for anomaly detection")
            return []

        anomalies = []

        # Extract amounts as 2D array for Isolation Forest
        amounts = np.array([[float(tx.get('amount', 0))] for tx in transactions])

        # Train Isolation Forest model on transaction amounts
        try:
            self.model = IForest(
                contamination=self.contamination,
                random_state=self.random_state
            )
            self.model.fit(amounts)
            logger.debug("Isolation Forest model trained successfully")
        except Exception as e:
            logger.error(f"Failed to train Isolation Forest: {e}", exc_info=True)
            return []

        # Evaluate each transaction
        for i, transaction in enumerate(transactions):
            amount = float(transaction.get('amount', 0))
            tx_id = transaction.get('transaction_id', i + 1)

            # Rule 1: Isolation Forest statistical outlier
            prediction = self.model.predict(amounts[i:i+1])[0]
            if prediction == 1:  # 1 = outlier, 0 = inlier
                severity = "high" if amount > OUTLIER_AMOUNT_THRESHOLD else "medium"
                anomalies.append({
                    "type": "outlier",
                    "transaction_id": tx_id,
                    "amount": amount,
                    "severity": severity,
                    "message": f"Statistically unusual transaction amount: ${amount:,.2f}"
                })

            # Rule 2: Round-dollar transactions (potential structuring)
            # Uses configurable threshold; default $1,000
            if amount >= ROUND_DOLLAR_THRESHOLD and self._is_round_dollar(amount):
                severity = "high" if amount >= 10000 else "medium"
                anomalies.append({
                    "type": "round_dollar",
                    "transaction_id": tx_id,
                    "amount": amount,
                    "severity": severity,
                    "message": f"Round-dollar transaction (possible structuring): ${amount:,.2f}"
                })

            # Rule 3: Very high-value transactions (absolute threshold)
            if amount > 250000:
                anomalies.append({
                    "type": "high_value",
                    "transaction_id": tx_id,
                    "amount": amount,
                    "severity": "high",
                    "message": f"Very high-value transaction: ${amount:,.2f}"
                })

        logger.info(f"Detected {len(anomalies)} anomalies across {len(transactions)} transactions")
        return anomalies

    @staticmethod
    def _is_round_dollar(amount: float, threshold: float = None) -> bool:
        """
        Check if amount is a round number (multiple of 1000).

        Args:
            amount: Transaction amount
            threshold: Minimum amount to consider (default from config)

        Returns:
            True if amount is round-dollar at or above threshold
        """
        if threshold is None:
            from src.utils.config import ROUND_DOLLAR_THRESHOLD
            threshold = ROUND_DOLLAR_THRESHOLD
        return amount >= threshold and round(amount) == amount and (amount % 1000 == 0)


def detect_anomalies(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convenience function for anomaly detection."""
    detector = AnomalyDetector()
    return detector.detect_anomalies(transactions)
