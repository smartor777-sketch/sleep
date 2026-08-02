"""API эндпоинты администратора."""

import logging
import secrets

from fastapi import APIRouter, HTTPException, Query, status

from dependencies import AdminUser, DatabaseSession
from models import Analysis, Dream, User
from schemas import (
    AdminResetPasswordResponse,
    AdminStatsResponse,
    AdminUserCreate,
    AdminUserListResponse,
    AdminUserListItem,
    AdminUserUpdate,
)
from services.auth_service import get_password_hash

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def admin_stats(db: DatabaseSession, _admin: AdminUser):
    from sqlalchemy import func, select

    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_dreams = (await db.execute(select(func.count(Dream.id)))).scalar() or 0
    total_analyses = (await db.execute(select(func.count(Analysis.id)))).scalar() or 0
    total_anonymous = (
        await db.execute(
            select(func.count(User.id)).where(User.is_anonymous.is_(True))
        )
    ).scalar() or 0
    total_premium = (
        await db.execute(
            select(func.count(User.id)).where(User.sub_type.in_(["premium", "pro"]))
        )
    ).scalar() or 0

    from datetime import datetime, timedelta

    week_ago = datetime.utcnow() - timedelta(days=7)
    active_last_7d = (
        await db.execute(
            select(func.count(User.id)).where(User.last_login_at >= week_ago)
        )
    ).scalar() or 0

    return AdminStatsResponse(
        total_users=total_users,
        total_dreams=total_dreams,
        total_analyses=total_analyses,
        total_anonymous=total_anonymous,
        total_premium=total_premium,
        active_last_7d=active_last_7d,
    )


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    db: DatabaseSession,
    _admin: AdminUser,
    q: str | None = Query(None, max_length=200),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    from sqlalchemy import func, or_, select

    base = select(User)
    count_q = select(func.count(User.id))
    if q:
        like = f"%{q}%"
        cond = or_(
            User.email.ilike(like),
            User.first_name.ilike(like),
            User.last_name.ilike(like),
            User.device_id.ilike(like),
        )
        base = base.where(cond)
        count_q = count_q.where(cond)

    total = (await db.execute(count_q)).scalar() or 0

    rows = (
        (
            await db.execute(
                base.order_by(User.created_at.desc()).offset(offset).limit(limit)
            )
        )
        .scalars()
        .all()
    )

    # Число снов для отображения списком
    dream_counts: dict[str, int] = {}
    if rows:
        from sqlalchemy import select

        counts_q = (
            select(Dream.user_id, func.count(Dream.id))
            .where(Dream.user_id.in_([u.id for u in rows]))
            .group_by(Dream.user_id)
        )
        for uid, cnt in (await db.execute(counts_q)).all():
            dream_counts[str(uid)] = cnt

    items = [
        AdminUserListItem(
            id=u.id,
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            is_active=u.is_active,
            is_admin=u.is_admin,
            is_anonymous=u.is_anonymous,
            email_verified=u.email_verified,
            sub_type=u.sub_type,
            created_at=u.created_at,
            last_login_at=u.last_login_at,
            dreams_count=dream_counts.get(str(u.id), 0),
        )
        for u in rows
    ]

    return AdminUserListResponse(total=total, items=items)


@router.post("/users", response_model=AdminUserListItem, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: AdminUserCreate,
    db: DatabaseSession,
    _admin: AdminUser,
):
    from sqlalchemy import select

    from services.auth_service import get_user_by_email

    if await get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        timezone="UTC",
        is_anonymous=False,
        email_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return AdminUserListItem(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        is_anonymous=user.is_anonymous,
        email_verified=user.email_verified,
        sub_type=user.sub_type,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        dreams_count=0,
    )


@router.patch("/users/{user_id}", response_model=AdminUserListItem)
async def update_user(
    user_id: str,
    data: AdminUserUpdate,
    db: DatabaseSession,
    admin: AdminUser,
):
    from uuid import UUID

    try:
        uid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user id",
        )

    user = await db.get(User, uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == admin.id and data.is_admin is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin rights",
        )

    update = data.model_dump(exclude_unset=True)
    for field, value in update.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return AdminUserListItem(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        is_anonymous=user.is_anonymous,
        email_verified=user.email_verified,
        sub_type=user.sub_type,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        dreams_count=0,
    )


@router.post("/users/{user_id}/reset-password", response_model=AdminResetPasswordResponse)
async def reset_password(
    user_id: str,
    db: DatabaseSession,
    _admin: AdminUser,
):
    from uuid import UUID

    try:
        uid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user id",
        )

    user = await db.get(User, uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    new_password = secrets.token_urlsafe(10)
    user.password_hash = get_password_hash(new_password)
    await db.commit()

    return AdminResetPasswordResponse(
        user_id=user.id,
        email=user.email,
        new_password=new_password,
    )
