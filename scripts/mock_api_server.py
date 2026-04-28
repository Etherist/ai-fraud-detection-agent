"""Mock API Server - Simulates ABR and ATO APIs for demo purposes."""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

# Initialize mock FastAPI app
mock_app = FastAPI(
    title="Mock ABR/ATO APIs",
    description="Mock Australian Business Register (ABR) and Australian Taxation Office (ATO) APIs for demo.",
    version="1.0.0"
)

# Enable CORS
mock_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ABRResponse(BaseModel):
    """Mock ABR lookup response."""
    valid: bool
    abn: str
    name: str
    status: str
    registration_date: str
    address: str
    entity_type: str
    message: str


class ATOResponse(BaseModel):
    """Mock ATO lookup response."""
    abn: str
    tax_return_filed: bool
    reported_revenue: float
    taxable_income: float
    financial_year: str
    message: str


@mock_app.get("/abr")
async def abr_lookup(abn: str, name: str) -> ABRResponse:
    """
    Mock ABR business validation endpoint.

    Logic:
    - ABNs starting with '123' are VALID
    - ABNs starting with '999' are INVALID (shell companies)
    - ABNs starting with '888' are SUSPENDED
    - All others return as 'Unknown'
    """
    logger.info(f"Mock ABR lookup: ABN={abn}, Name={name}")

    if not abn or not name:
        raise HTTPException(status_code=400, detail="ABN and name required")

    # Pad/truncate to 11 digits
    abn_clean = abn.strip().zfill(11)[:11]

    # Determine validity based on mock rules
    if abn_clean.startswith('123'):
        valid = True
        status = "Active"
        registration_date = "2020-01-01"
        entity_type = "Australian Proprietary Company"
        message = "ABN validation successful"
    elif abn_clean.startswith('999'):
        valid = False
        status = "Cancelled"
        registration_date = "N/A"
        entity_type = "Unknown"
        message = "ABN cancelled - potential shell company"
    elif abn_clean.startswith('888'):
        valid = False
        status = "Suspended"
        registration_date = "2018-05-15"
        entity_type = "Australian Proprietary Company"
        message = "ABN suspended - compliance issues"
    else:
        valid = True  # Default to valid for demo
        status = "Active"
        registration_date = "2021-03-01"
        entity_type = "Australian Proprietary Company"
        message = "ABN validation successful"

    return ABRResponse(
        valid=valid,
        abn=abn_clean,
        name=name,
        status=status,
        registration_date=registration_date,
        address="123 Mock Street, Sydney NSW 2000, Australia",
        entity_type=entity_type,
        message=message
    )


@mock_app.get("/ato")
async def ato_lookup(abn: str, financial_year: str = "2025") -> ATOResponse:
    """
    Mock ATO tax return lookup endpoint.

    Logic:
    - ABNs starting with '123' have filed returns with good revenue
    - ABNs starting with '999' have no tax return filed
    - ABNs starting with '888' have inconsistent filings
    """
    logger.info(f"Mock ATO lookup: ABN={abn}, FY={financial_year}")

    if not abn:
        raise HTTPException(status_code=400, detail="ABN required")

    abn_clean = abn.strip().zfill(11)[:11]

    if abn_clean.startswith('123'):
        tax_return_filed = True
        reported_revenue = 750000.00
        taxable_income = 520000.00
        message = "Tax return verified - consistent with bank statement"
    elif abn_clean.startswith('999'):
        tax_return_filed = False
        reported_revenue = 0.0
        taxable_income = 0.0
        message = "No tax return filed - high risk"
    elif abn_clean.startswith('888'):
        tax_return_filed = True
        reported_revenue = 1500000.00  # Mismatch expected with bank
        taxable_income = 1200000.00
        message = "Tax return filed but revenue mismatch detected"
    else:
        tax_return_filed = True
        reported_revenue = 500000.00
        taxable_income = 350000.00
        message = "Tax return on file"

    return ATOResponse(
        abn=abn_clean,
        tax_return_filed=tax_return_filed,
        reported_revenue=reported_revenue,
        taxable_income=taxable_income,
        financial_year=financial_year,
        message=message
    )


@mock_app.get("/health")
async def mock_health():
    """Health check for mock API."""
    return {"status": "healthy", "service": "mock-abr-ato"}


# Export for running with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mock_app, host="0.0.0.0", port=8001)
