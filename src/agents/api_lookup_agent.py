"""API Lookup Agent - Validates business details via mock ABR/ATO APIs."""

import logging
from typing import Dict, Any, Optional, List
import httpx

from src.utils.config import MOCK_ABR_API_URL, MOCK_ATO_API_URL

logger = logging.getLogger(__name__)


class APILookupAgent:
    """Agent for performing real-time API lookups to validate business details (ABR/ATO)."""

    def __init__(self, abr_url: str = None, ato_url: str = None, timeout: int = 5):
        """
        Initialize API Lookup Agent.

        Args:
            abr_url: Mock ABR API endpoint URL (defaults to config)
            ato_url: Mock ATO API endpoint URL (defaults to config)
            timeout: Request timeout in seconds
        """
        self.abr_url = abr_url or MOCK_ABR_API_URL
        self.ato_url = ato_url or MOCK_ATO_API_URL
        self.timeout = timeout
        logger.info(f"APILookupAgent initialized - ABR: {self.abr_url}, ATO: {self.ato_url}")

    def lookup_business(self, abn: str, business_name: str) -> Dict[str, Any]:
        """
        Validate business details via mock ABR API.

        Args:
            abn: Australian Business Number
            business_name: Business name to validate

        Returns:
            Dictionary with validation results.
        """
        logger.info(f"Looking up business: ABN={abn}, Name={business_name}")

        if not abn or not business_name:
            return {
                "valid": False,
                "message": "ABN and business name required",
                "abn": abn,
                "name": business_name
            }

        try:
            response = httpx.get(
                self.abr_url,
                params={"abn": abn, "name": business_name},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            result = {
                "valid": data.get("valid", False),
                "abn": abn,
                "name": business_name,
                "status": data.get("status", "Unknown"),
                "registration_date": data.get("registration_date", "N/A"),
                "address": data.get("address", "N/A"),
                "entity_type": data.get("entity_type", "N/A"),
                "message": "ABR validation successful" if data.get("valid") else "ABR validation failed"
            }

            logger.info(f"ABR lookup result: valid={result['valid']}")
            return result

        except httpx.RequestError as e:
            logger.error(f"ABR API request failed: {e}")
            return {
                "valid": False,
                "abn": abn,
                "name": business_name,
                "message": "ABR API unavailable",
                "status": "Error"
            }

    def lookup_tax_return(self, abn: str, financial_year: str = "2025") -> Dict[str, Any]:
        """
        Validate tax return via mock ATO API.

        Args:
            abn: Australian Business Number
            financial_year: Financial year to lookup

        Returns:
            Dictionary with tax return validation results.
        """
        logger.info(f"Looking up tax return: ABN={abn}, FY={financial_year}")

        try:
            response = httpx.get(
                self.ato_url,
                params={"abn": abn, "financial_year": financial_year},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            result = {
                "found": data.get("tax_return_filed", False),
                "abn": abn,
                "financial_year": financial_year,
                "reported_revenue": data.get("reported_revenue", 0),
                "taxable_income": data.get("taxable_income", 0),
                "message": data.get("message", "Tax return found") if data.get("tax_return_filed") else "No tax return filed"
            }

            logger.info(f"ATO lookup result: found={result['found']}")
            return result

        except httpx.RequestError as e:
            logger.error(f"ATO API request failed: {e}")
            return {
                "found": False,
                "abn": abn,
                "financial_year": financial_year,
                "message": "ATO API unavailable"
            }

    def batch_lookup(self, businesses: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Perform batch lookup for multiple businesses.

        Args:
            businesses: List of {"abn": str, "business_name": str} dicts

        Returns:
            Dictionary with results for each business
        """
        results = []
        for business in businesses:
            abn = business.get('abn', '')
            name = business.get('business_name', '')
            result = self.lookup_business(abn, name)
            results.append(result)

        return {
            "batch_size": len(businesses),
            "valid_count": sum(1 for r in results if r.get('valid', False)),
            "results": results
        }


def lookup_business(abn: str, business_name: str) -> Dict[str, Any]:
    """Convenience function for single business lookup."""
    agent = APILookupAgent()
    return agent.lookup_business(abn, business_name)


def lookup_tax_return(abn: str) -> Dict[str, Any]:
    """Convenience function for tax return lookup."""
    agent = APILookupAgent()
    return agent.lookup_tax_return(abn)
