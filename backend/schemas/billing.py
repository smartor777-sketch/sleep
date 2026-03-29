"""Pydantic схемы для биллинга"""

from datetime import datetime
from pydantic import BaseModel


class VerifyPurchaseRequest(BaseModel):
    purchase_token: str
    product_id: str


class SubscriptionInfo(BaseModel):
    product_id: str
    expires_at: str


class BillingStatusResponse(BaseModel):
    sub_type: str
    sub_expires_at: str | None = None
    trial_days_left: int = 0
    analyses_left_this_week: int | None = None
    active_subscription: SubscriptionInfo | None = None


class VerifyPurchaseResponse(BaseModel):
    status: str
    product_id: str
    expires_at: datetime
