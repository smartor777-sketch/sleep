"""Сервис биллинга — верификация покупок Google Play"""

import logging
from datetime import datetime, timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.subscription import Subscription
from models.user import User

logger = logging.getLogger(__name__)

# Google Play Developer API client (singleton)
_play_client = None


def _get_play_client():
    """Lazy-init Google Play Developer API client."""
    global _play_client
    if _play_client is not None:
        return _play_client

    sa_json = settings.google_play_service_account_json
    if not sa_json:
        raise RuntimeError("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON not configured")

    import json
    info = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/androidpublisher"],
    )
    _play_client = build("androidpublisher", "v3", credentials=creds, cache_discovery=False)
    return _play_client


async def verify_purchase(
    db: AsyncSession,
    user: User,
    purchase_token: str,
    product_id: str,
) -> Subscription:
    """
    Verify a Google Play subscription purchase and record it.
    Returns the created/updated Subscription row.
    """
    package_name = settings.google_play_package_name
    client = _get_play_client()

    # Call Google Play Developer API
    result = client.purchases().subscriptions().get(
        packageName=package_name,
        subscriptionId=product_id,
        token=purchase_token,
    ).execute()

    # Parse timestamps (millis since epoch)
    start_ms = int(result.get("startTimeMillis", 0))
    expiry_ms = int(result.get("expiryTimeMillis", 0))
    starts_at = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc)
    expires_at = datetime.fromtimestamp(expiry_ms / 1000, tz=timezone.utc)

    # Determine status
    cancel_reason = result.get("cancelReason")
    payment_state = result.get("paymentState")
    if cancel_reason is not None:
        status = "cancelled"
    elif expires_at < datetime.now(timezone.utc):
        status = "expired"
    else:
        status = "active"

    # Upsert subscription
    existing = await db.execute(
        select(Subscription).where(Subscription.purchase_token == purchase_token)
    )
    sub = existing.scalar_one_or_none()

    if sub:
        sub.status = status
        sub.expires_at = expires_at
        sub.updated_at = datetime.now(timezone.utc)
    else:
        sub = Subscription(
            user_id=user.id,
            provider="google_play",
            product_id=product_id,
            purchase_token=purchase_token,
            status=status,
            starts_at=starts_at,
            expires_at=expires_at,
        )
        db.add(sub)

    # Update user sub_type
    if status == "active":
        user.sub_type = "pro"
        user.sub_expires_at = expires_at
    elif status in ("cancelled", "expired"):
        # Check if user has any other active subs
        other_active = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.status == "active",
                Subscription.purchase_token != purchase_token,
            )
        )
        if not other_active.scalar_one_or_none():
            user.sub_type = "free"
            user.sub_expires_at = None

    await db.commit()
    await db.refresh(sub)
    return sub


async def get_billing_status(db: AsyncSession, user: User) -> dict:
    """Return current billing status for user."""
    now = datetime.now(timezone.utc)

    # Trial days left
    trial_days_left = 0
    if user.sub_type == "trial" and user.trial_started_at:
        elapsed = (now - user.trial_started_at).days
        trial_days_left = max(0, 7 - elapsed)

    # Analyses left this week (for free users)
    analyses_left = None
    if user.sub_type == "free":
        # Reset weekly counter if needed
        if user.analyses_week_reset_at is None or (now - user.analyses_week_reset_at).days >= 7:
            user.analyses_week_count = 0
            user.analyses_week_reset_at = now
            await db.commit()
        analyses_left = max(0, 2 - user.analyses_week_count)

    # Active subscription info
    active_sub = None
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.status == "active",
        ).order_by(Subscription.expires_at.desc())
    )
    sub = result.scalar_one_or_none()
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


async def handle_rtdn_notification(db: AsyncSession, message_data: dict) -> None:
    """
    Handle Google Play Real-Time Developer Notification.
    Called from webhook endpoint.
    """
    subscription_notification = message_data.get("subscriptionNotification")
    if not subscription_notification:
        logger.info("RTDN: not a subscription notification, skipping")
        return

    purchase_token = subscription_notification.get("purchaseToken")
    product_id = subscription_notification.get("subscriptionId")
    notification_type = subscription_notification.get("notificationType")

    if not purchase_token or not product_id:
        logger.warning("RTDN: missing purchaseToken or subscriptionId")
        return

    logger.info(f"RTDN: type={notification_type}, product={product_id}")

    # Find existing subscription
    result = await db.execute(
        select(Subscription).where(Subscription.purchase_token == purchase_token)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        logger.warning(f"RTDN: unknown purchase_token, skipping")
        return

    # Load user
    user_result = await db.execute(select(User).where(User.id == sub.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return

    # Re-verify with Google to get fresh state
    try:
        await verify_purchase(db, user, purchase_token, product_id)
    except Exception:
        logger.exception("RTDN: failed to re-verify purchase")
