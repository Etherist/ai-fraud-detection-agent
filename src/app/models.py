"""Data models for FastAPI application."""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class Transaction(BaseModel):
    """Transaction data model."""
    transaction_id: int
    date: str
    amount: float = Field(..., gt=0)
    description: str = ""
    business_name: Optional[str] = None
    abn: Optional[str] = None
    counterparty_jurisdiction: Optional[str] = None
    counterparty: Optional[str] = None

    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v


class BusinessDetails(BaseModel):
    """Business information model."""
    business_name: str
    abn: str = ""
    addresses: List[str] = []
    registration_date: Optional[str] = None
    entity_type: Optional[str] = None


class Anomaly(BaseModel):
    """Detected anomaly model."""
    type: str
    transaction_id: int
    amount: float
    severity: str
    message: str


class AMLAlert(BaseModel):
    """AML alert model."""
    type: str
    transaction_id: Optional[int] = None
    severity: str
    message: str
    detail: Optional[str] = None


class APRAFields(BaseModel):
    """APRA APS 222 compliance fields."""
    asset_classification: str
    impairment_provision: float
    regulatory_code: str
    collateral_value: float
    loan_to_value_ratio: float
    requires_manual_review: bool
    review_priority: str
    apra_reporting_category: str


class RiskScore(BaseModel):
    """Risk scoring result model."""
    score: int = Field(..., ge=0, le=100)
    category: str
    breakdown: Dict[str, int]
    apra_fields: APRAFields


class AnalysisResult(BaseModel):
    """Complete analysis result model."""
    task_id: str
    status: str
    risk_score: int
    category: str
    anomalies: List[Dict[str, Any]]
    aml_alerts: List[Dict[str, Any]]
    apra_fields: Dict[str, Any]
    report_url: Optional[str] = None
    processed_at: Optional[str] = None


class AnalysisRequest(BaseModel):
    """Analysis request model."""
    business_name: Optional[str] = None
    abn: Optional[str] = None
    upload_id: Optional[str] = None


class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str = "1.0.0"
