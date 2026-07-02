from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from services import billing_service
from tests.helpers import FakeDb, FakeResult


@pytest.mark.asyncio
async def test_billing_status_expires_trial_without_erasing_trial_marker():
    started_at = datetime.now(timezone.utc) - timedelta(days=15)
    user = SimpleNamespace(
        id=uuid4(),
        sub_type="trial",
        trial_started_at=started_at,
        sub_expires_at=None,
        analyses_week_count=0,
        analyses_week_reset_at=None,
    )
    db = FakeDb(execute_results=[FakeResult(scalar=None)])

    status = await billing_service.get_billing_status(db, user)

    assert user.sub_type == "free"
    assert user.trial_started_at == started_at
    assert status["sub_type"] == "free"
    assert status["trial_days_left"] == 0
    assert status["analyses_left_this_week"] == 2
    assert db.commits == 2


@pytest.mark.asyncio
async def test_has_full_access_expires_stale_pro_without_active_subscription():
    user = SimpleNamespace(
        id=uuid4(),
        sub_type="pro",
        sub_expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        trial_started_at=None,
    )
    db = FakeDb(execute_results=[FakeResult(scalar=None)])

    assert await billing_service.has_full_access(db, user) is False
    assert user.sub_type == "free"
    assert user.sub_expires_at is None
    assert db.commits == 1


@pytest.mark.asyncio
async def test_create_payment_records_pending_yookassa_subscription(monkeypatch):
    user = SimpleNamespace(id=uuid4(), sub_type="free", sub_expires_at=None)

    async def fake_yookassa_request(method, path, *, json_payload=None, idempotence_key=None):
        assert method == "POST"
        assert path == "/payments"
        assert json_payload["amount"] == {"value": "749.00", "currency": "RUB"}
        assert json_payload["metadata"]["user_id"] == str(user.id)
        assert json_payload["metadata"]["plan_id"] == "monthly"
        assert idempotence_key
        return {
            "id": "payment-1",
            "status": "pending",
            "paid": False,
            "confirmation": {"confirmation_url": "https://yookassa.example/pay"},
        }

    monkeypatch.setattr(billing_service, "_yookassa_request", fake_yookassa_request)
    db = FakeDb(execute_results=[FakeResult(scalar=None)])

    result = await billing_service.create_payment(db, user, "monthly")

    assert result["payment_id"] == "payment-1"
    assert result["confirmation_url"] == "https://yookassa.example/pay"
    assert db.added[0].provider == "yookassa"
    assert db.added[0].provider_payment_id == "payment-1"
    assert db.added[0].status == "pending"


@pytest.mark.asyncio
async def test_activate_yookassa_payment_sets_user_pro():
    user = SimpleNamespace(id=uuid4(), sub_type="free", sub_expires_at=None)
    payment = {
        "id": "payment-1",
        "status": "succeeded",
        "paid": True,
        "metadata": {"user_id": str(user.id), "plan_id": "quarter"},
    }
    db = FakeDb(execute_results=[FakeResult(scalar=user), FakeResult(scalar=None)])

    sub = await billing_service.activate_yookassa_payment(db, payment)

    assert sub is db.added[0]
    assert sub.status == "active"
    assert sub.product_id == "quarter"
    assert sub.provider_payment_id == "payment-1"
    assert user.sub_type == "pro"
    assert user.sub_expires_at == sub.expires_at
    assert sub.expires_at > sub.starts_at
    assert db.commits == 1
