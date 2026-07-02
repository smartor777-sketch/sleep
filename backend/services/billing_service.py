"""Сервис биллинга: YooKassa payments, тарифы и доступ."""

from __future__ import annotations

import calendar
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.subscription import Subscription
from models.user import User

logger = logging.getLogger(__name__)


TRIAL_DURATION_DAYS = 14
PROVIDER_YOOKASSA = "yookassa"


@dataclass(frozen=True)
class BillingPlan:
    id: str
    months: int
    amount_rub: Decimal
    title_ru: str

    @property
    def amount_value(self) -> str:
        return f"{self.amount_rub:.2f}"


PLANS: dict[str, BillingPlan] = {
    "monthly": BillingPlan("monthly", 1, Decimal("749.00"), "InnerCore Pro на 1 месяц"),
    "quarter": BillingPlan("quarter", 3, Decimal("1899.00"), "InnerCore Pro на 3 месяца"),
    "half": BillingPlan("half", 6, Decimal("2999.00"), "InnerCore Pro на 6 месяцев"),
    "yearly": BillingPlan("yearly", 12, Decimal("5249.00"), "InnerCore Pro на 12 месяцев"),
}

PLAN_ALIASES = {
    "pro_monthly": "monthly",
    "pro_quarter": "quarter",
    "pro_half": "half",
    "pro_yearly": "yearly",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _current_paid_until(user: User) -> datetime | None:
    expires_at = _as_utc(user.sub_expires_at)
    if user.sub_type == "pro" and expires_at and expires_at > _now():
        return expires_at
    return None


def _add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def normalize_plan_id(plan_id: str) -> str:
    normalized = plan_id.strip().lower()
    normalized = PLAN_ALIASES.get(normalized, normalized)
    if normalized not in PLANS:
        raise ValueError("invalid_plan")
    return normalized


def get_plan(plan_id: str) -> BillingPlan:
    return PLANS[normalize_plan_id(plan_id)]


def _require_yookassa_settings() -> tuple[str, str]:
    shop_id = settings.yookassa_shop_id
    secret = settings.yookassa_secret_key.get_secret_value() if settings.yookassa_secret_key else None
    if not shop_id or not secret:
        raise RuntimeError("YOOKASSA_SHOP_ID/YOOKASSA_SECRET_KEY not configured")
    return shop_id, secret


def _build_receipt(user: User, plan: BillingPlan) -> dict[str, Any] | None:
    if not settings.yookassa_receipts_enabled:
        return None

    email = getattr(user, "email", None)
    if not email:
        raise RuntimeError("user_email_required_for_receipt")

    receipt = {
        "customer": {"email": email},
        "items": [
            {
                "description": plan.title_ru,
                "quantity": "1.00",
                "amount": {"value": plan.amount_value, "currency": "RUB"},
                "vat_code": settings.yookassa_vat_code,
                "payment_mode": "full_payment",
                "payment_subject": "service",
            }
        ],
    }
    if settings.yookassa_tax_system_code is not None:
        receipt["tax_system_code"] = settings.yookassa_tax_system_code
    return receipt


async def _yookassa_request(
    method: str,
    path: str,
    *,
    json_payload: dict[str, Any] | None = None,
    idempotence_key: str | None = None,
) -> dict[str, Any]:
    shop_id, secret = _require_yookassa_settings()
    headers = {"Accept": "application/json"}
    if idempotence_key:
        headers["Idempotence-Key"] = idempotence_key

    async with httpx.AsyncClient(
        base_url=settings.yookassa_api_url.rstrip("/"),
        auth=(shop_id, secret),
        headers=headers,
        timeout=30,
    ) as client:
        response = await client.request(method, path, json=json_payload)

    if response.status_code >= 400:
        logger.warning("YooKassa request failed: %s %s", response.status_code, response.text)
        response.raise_for_status()
    return response.json()


async def create_payment(
    db: AsyncSession,
    user: User,
    plan_id: str,
    return_url: str | None = None,
) -> dict[str, Any]:
    """Create a YooKassa redirect payment for a fixed Pro access period."""
    plan = get_plan(plan_id)
    target_return_url = return_url or settings.yookassa_return_url
    idempotence_key = str(uuid.uuid4())

    payload = {
        "amount": {"value": plan.amount_value, "currency": "RUB"},
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": target_return_url,
        },
        "description": plan.title_ru,
        "metadata": {
            "user_id": str(user.id),
            "plan_id": plan.id,
            "months": str(plan.months),
        },
    }
    receipt = _build_receipt(user, plan)
    if receipt is not None:
        payload["receipt"] = receipt

    payment = await _yookassa_request(
        "POST",
        "/payments",
        json_payload=payload,
        idempotence_key=idempotence_key,
    )

    payment_id = payment["id"]
    confirmation_url = (payment.get("confirmation") or {}).get("confirmation_url")
    if not confirmation_url:
        raise RuntimeError("YooKassa did not return confirmation_url")

    existing = await db.execute(
        select(Subscription).where(Subscription.provider_payment_id == payment_id)
    )
    sub = existing.scalar_one_or_none()
    planned_start = _current_paid_until(user) or _now()
    planned_end = _add_months(planned_start, plan.months)

    if sub is None:
        sub = Subscription(
            user_id=user.id,
            provider=PROVIDER_YOOKASSA,
            product_id=plan.id,
            provider_payment_id=payment_id,
            status="pending",
            starts_at=planned_start,
            expires_at=planned_end,
        )
        db.add(sub)
        await db.commit()

    if payment.get("paid") is True and payment.get("status") == "succeeded":
        sub = await activate_yookassa_payment(db, payment)

    return {
        "payment_id": payment_id,
        "status": payment.get("status", "pending"),
        "plan_id": plan.id,
        "confirmation_url": confirmation_url,
        "expires_at": sub.expires_at if sub and sub.status == "active" else None,
    }


async def fetch_yookassa_payment(payment_id: str) -> dict[str, Any]:
    """Fetch payment from YooKassa and use it as the source of truth."""
    return await _yookassa_request("GET", f"/payments/{payment_id}")


async def activate_yookassa_payment(db: AsyncSession, payment: dict[str, Any]) -> Subscription | None:
    """Idempotently activate a paid YooKassa payment."""
    if payment.get("status") != "succeeded" or payment.get("paid") is not True:
        return None

    payment_id = payment.get("id")
    metadata = payment.get("metadata") or {}
    user_id_raw = metadata.get("user_id")
    plan_id_raw = metadata.get("plan_id")
    if not payment_id or not user_id_raw or not plan_id_raw:
        logger.warning("YooKassa payment missing metadata: id=%s", payment_id)
        return None

    try:
        user_id = UUID(str(user_id_raw))
        plan = get_plan(str(plan_id_raw))
    except (ValueError, TypeError):
        logger.warning("YooKassa payment has invalid metadata: id=%s", payment_id)
        return None

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        logger.warning("YooKassa payment user not found: id=%s user=%s", payment_id, user_id)
        return None

    existing = await db.execute(
        select(Subscription).where(Subscription.provider_payment_id == payment_id)
    )
    sub = existing.scalar_one_or_none()
    if sub is not None and sub.status == "active":
        if user.sub_type != "pro" or not user.sub_expires_at or user.sub_expires_at < sub.expires_at:
            user.sub_type = "pro"
            user.sub_expires_at = sub.expires_at
            await db.commit()
        return sub

    start_at = _current_paid_until(user) or _now()
    expires_at = _add_months(start_at, plan.months)

    if sub is None:
        sub = Subscription(
            user_id=user.id,
            provider=PROVIDER_YOOKASSA,
            product_id=plan.id,
            provider_payment_id=payment_id,
            status="active",
            starts_at=start_at,
            expires_at=expires_at,
        )
        db.add(sub)
    else:
        sub.provider = PROVIDER_YOOKASSA
        sub.product_id = plan.id
        sub.status = "active"
        sub.starts_at = start_at
        sub.expires_at = expires_at
        sub.updated_at = _now()

    user.sub_type = "pro"
    user.sub_expires_at = expires_at
    await db.commit()
    await db.refresh(sub)
    return sub


async def cancel_yookassa_payment(db: AsyncSession, payment_id: str) -> None:
    result = await db.execute(
        select(Subscription).where(Subscription.provider_payment_id == payment_id)
    )
    sub = result.scalar_one_or_none()
    if sub is None or sub.status == "active":
        return
    sub.status = "cancelled"
    sub.updated_at = _now()
    await db.commit()


async def handle_yookassa_webhook(db: AsyncSession, payload: dict[str, Any]) -> dict[str, str]:
    """Handle YooKassa webhook by re-fetching the payment from YooKassa."""
    event = payload.get("event")
    obj = payload.get("object") or {}
    payment_id = obj.get("id")
    if not payment_id:
        return {"status": "ignored"}

    if event == "payment.succeeded":
        payment = await fetch_yookassa_payment(str(payment_id))
        sub = await activate_yookassa_payment(db, payment)
        return {"status": "ok" if sub else "ignored"}

    if event == "payment.canceled":
        await cancel_yookassa_payment(db, str(payment_id))
        return {"status": "ok"}

    return {"status": "ignored"}


async def refresh_entitlements(db: AsyncSession, user: User) -> None:
    """Keep user.sub_type synchronized with trial/pro expiry dates."""
    now = _now()
    changed = False
    sub_type = getattr(user, "sub_type", "free")

    if sub_type == "trial" and getattr(user, "trial_started_at", None):
        trial_started_at = _as_utc(user.trial_started_at)
        if (now - trial_started_at).days >= TRIAL_DURATION_DAYS:
            user.sub_type = "free"
            sub_type = "free"
            changed = True

    if sub_type == "pro" and getattr(user, "sub_expires_at", None):
        sub_expires_at = _as_utc(user.sub_expires_at)
        if sub_expires_at <= now:
            result = await db.execute(
                select(Subscription)
                .where(
                    Subscription.user_id == user.id,
                    Subscription.status == "active",
                    Subscription.expires_at > now,
                )
                .order_by(Subscription.expires_at.desc())
            )
            active_sub = (result.scalars().all() or [None])[0]
            if active_sub:
                user.sub_expires_at = active_sub.expires_at
            else:
                user.sub_type = "free"
                user.sub_expires_at = None
                sub_type = "free"
            changed = True

    if changed:
        await db.commit()
        await db.refresh(user)


async def has_full_access(db: AsyncSession, user: User) -> bool:
    await refresh_entitlements(db, user)
    return getattr(user, "sub_type", "free") in ("pro", "trial")


async def get_billing_status(db: AsyncSession, user: User) -> dict:
    """Return current billing status for user."""
    await refresh_entitlements(db, user)
    now = _now()

    trial_days_left = 0
    if user.sub_type == "trial" and user.trial_started_at:
        trial_started_at = _as_utc(user.trial_started_at)
        elapsed = (now - trial_started_at).days
        trial_days_left = max(0, TRIAL_DURATION_DAYS - elapsed)

    analyses_left = None
    if user.sub_type == "free":
        if user.analyses_week_reset_at is None or (now - user.analyses_week_reset_at).days >= 7:
            user.analyses_week_count = 0
            user.analyses_week_reset_at = now
            await db.commit()
        analyses_left = max(0, 2 - user.analyses_week_count)

    active_sub = None
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.user_id == user.id,
            Subscription.status == "active",
            Subscription.expires_at > now,
        )
        .order_by(Subscription.expires_at.desc())
    )
    sub = (result.scalars().all() or [None])[0]
    if sub:
        active_sub = {
            "product_id": sub.product_id,
            "expires_at": sub.expires_at.isoformat(),
        }

    return {
        "sub_type": user.sub_type,
        "sub_expires_at": user.sub_expires_at.isoformat() if user.sub_expires_at else None,
        "trial_days_left": trial_days_left,
        "analyses_left_this_week": analyses_left,
        "active_subscription": active_sub,
    }


def start_trial(user: User) -> bool:
    """Start a one-shot trial for a fresh registered user."""
    if user.is_anonymous:
        return False
    # A freshly-constructed User() has no Python-side sub_type yet (only a
    # server_default), so it reads as None until the row round-trips the DB.
    if user.sub_type not in ("free", None):
        return False
    if user.trial_started_at is not None:
        return False

    user.sub_type = "trial"
    user.trial_started_at = _now()
    logger.info("Started %s-day trial for user %s", TRIAL_DURATION_DAYS, user.id)
    return True
