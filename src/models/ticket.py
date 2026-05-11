from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class TicketCategory(str, Enum):
    COMPUTE = "compute"
    NETWORKING = "networking"
    STORAGE = "storage"
    IDENTITY = "identity"
    AKS = "aks"
    BILLING = "billing"
    MONITORING = "monitoring"
    DEPLOYMENT = "deployment"
    OTHER = "other"


class TicketSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketSentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class Ticket(BaseModel):
    """Data model for a customer support ticket"""
    ticket_id: str = Field(..., description="Unique ticket identifier")
    customer_name: str = Field(..., description="Customer's name")
    customer_email: str = Field(..., description="Customer's email")
    subject: str = Field(..., description="Ticket subject")
    message: str = Field(..., description="Customer's message")
    created_at: datetime = Field(default_factory=datetime.now)

    # Analysis results (populated by agent)
    category: Optional[TicketCategory] = Field(None, description="Issue category")
    severity: Optional[TicketSeverity] = Field(None, description="Issue severity")
    key_issues: Optional[list[str]] = Field(None, description="Key issues identified")
    sentiment: Optional[TicketSentiment] = Field(None, description="Customer sentiment")

    class Config:
        use_enum_values = True
