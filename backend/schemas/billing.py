"""Pydantic схемы для биллинга"""

from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class CreatePaymentRequest(BaseModel):
    plan_id: str = Field(..., min_length=1, max_length=32)
    return_url: HttpUrl | None = None


class SubscriptionInfo(BaseModel):
    product_id: str
    expires_at: str


class BillingStatusResponse(BaseModel):
    sub_type: str
    sub_expires_at: str | None = None
    trial_days_left: int = 0
    analyses_left_this_week: int | None = None
    active_subscription: SubscriptionInfo | None = None


class CreatePaymentResponse(BaseModel):
    payment_id: str
    status: str
    plan_id: str
    confirmation_url: str
    expires_at: datetime | None = None
