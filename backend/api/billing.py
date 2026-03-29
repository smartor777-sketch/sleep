"""API эндпоинты для биллинга"""

import base64
import json
import logging

from fastapi import APIRouter, HTTPException, Request, status

from dependencies import DatabaseSession, CurrentUser
from schemas.billing import (
    VerifyPurchaseRequest,
    VerifyPurchaseResponse,
    BillingStatusResponse,
)
from services.billing_service import (
    verify_purchase,
    get_billing_status,
    handle_rtdn_notification,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/verify-purchase", response_model=VerifyPurchaseResponse)
async def verify_purchase_endpoint(
    data: VerifyPurchaseRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """Verify a Google Play purchase and activate subscription."""
    try:
        sub = await verify_purchase(
            db, current_user, data.purchase_token, data.product_id
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception:
        logger.exception("Failed to verify purchase")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="purchase_verification_failed",
        )
    return VerifyPurchaseResponse(
        status=sub.status,
        product_id=sub.product_id,
        expires_at=sub.expires_at,
    )


@router.get("/status", response_model=BillingStatusResponse)
async def billing_status(
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """Get current billing status for the authenticated user."""
    return await get_billing_status(db, current_user)


@router.post("/webhook")
async def google_play_webhook(request: Request, db: DatabaseSession):
    """
    Google Play Real-Time Developer Notification (RTDN) webhook.
    Google sends a Pub/Sub message with base64-encoded data.
    """
    try:
        body = await request.json()
        message = body.get("message", {})
        data_b64 = message.get("data", "")
        data_bytes = base64.b64decode(data_b64)
        message_data = json.loads(data_bytes)
    except Exception:
        logger.exception("RTDN: failed to parse webhook payload")
        # Return 200 so Google doesn't retry bad payloads forever
        return {"status": "parse_error"}

    await handle_rtdn_notification(db, message_data)
    return {"status": "ok"}
