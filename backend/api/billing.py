"""API эндпоинты для биллинга."""

import logging

from fastapi import APIRouter, HTTPException, Request, status

from dependencies import CurrentUser, DatabaseSession
from schemas.billing import (
    BillingStatusResponse,
    CreatePaymentRequest,
    CreatePaymentResponse,
)
from services.billing_service import (
    create_payment,
    get_billing_status,
    handle_yookassa_webhook,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/create-payment", response_model=CreatePaymentResponse)
async def create_payment_endpoint(
    data: CreatePaymentRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """Create a YooKassa redirect payment for the selected Pro plan."""
    try:
        return await create_payment(
            db,
            current_user,
            data.plan_id,
            str(data.return_url) if data.return_url else None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception:
        logger.exception("Failed to create YooKassa payment")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="payment_creation_failed",
        )


@router.get("/status", response_model=BillingStatusResponse)
async def billing_status(
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """Get current billing status for the authenticated user."""
    return await get_billing_status(db, current_user)


@router.post("/webhook")
async def yookassa_webhook(request: Request, db: DatabaseSession):
    """
    YooKassa webhook endpoint.

    The incoming JSON is not trusted as an entitlement source. The service
    re-fetches the payment from YooKassa before activating access.
    """
    try:
        payload = await request.json()
    except Exception:
        logger.exception("YooKassa webhook: failed to parse payload")
        return {"status": "parse_error"}

    try:
        return await handle_yookassa_webhook(db, payload)
    except RuntimeError:
        logger.exception("YooKassa webhook: billing provider is not configured")
        return {"status": "provider_not_configured"}
    except Exception:
        logger.exception("YooKassa webhook: failed to handle notification")
        return {"status": "error"}
