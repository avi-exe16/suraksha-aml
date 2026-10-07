from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TransactionInput(BaseModel):
    txn_id: str
    user_id: str
    amount: float
    channel: str = "UPI"
    ip_country: str = "IN"
    device_type: str = "mobile"
    is_weekend: int = 0
    hour: int = 12
    city: str = "Bengaluru"
    lat: float = 12.9716
    lon: float = 77.5946
    device_id: str = "DEV_DEFAULT"
    merchant_category: str = "general"
    sender_name: Optional[str] = None


class ConsentRevocation(BaseModel):
    user_id: str
    accessor: str


class RiskScoreResponse(BaseModel):
    txn_id: str
    user_id: str
    amount: float
    anomaly_score: float
    risk_level: str
    action: str
    shadow_mode: bool
    resilience: Dict[str, Any]
    sanctions_screening: Dict[str, Any]
    fiu_compliance: Dict[str, Any]
    explanation: List[Dict[str, Any]]
    timestamp: str