"""API эндпоинты для пользователя"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from dependencies import CurrentUser, DatabaseSession
from schemas import UserMeResponse, UserProfileResponse, UserSettingsUpdate
from services.oauth_identity_service import get_user_identities
from services import user_memory_service
from services.billing_service import refresh_entitlements
from services.auth_service import verify_password, get_password_hash

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: CurrentUser, db: DatabaseSession):
    await refresh_entitlements(db, current_user)
    identities = await get_user_identities(db, current_user)
    linked = sorted({i.provider for i in identities})

    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_anonymous=current_user.is_anonymous,
        is_admin=current_user.is_admin,
        email_verified=current_user.email_verified,
        sub_type=current_user.sub_type,
        linked_providers=linked,
        profile=UserProfileResponse(
            about_me=current_user.self_description,
            onboarding_completed=current_user.onboarding_completed,
        ),
    )


@router.put("/me", response_model=UserMeResponse)
async def update_me(
    data: UserSettingsUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    await refresh_entitlements(db, current_user)
    update = data.model_dump(exclude_unset=True)
    if "self_description" in update:
        current_user.self_description = update["self_description"]
    if "timezone" in update and update["timezone"]:
        current_user.timezone = update["timezone"]
    if "onboarding_completed" in update and update["onboarding_completed"] is not None:
        current_user.onboarding_completed = update["onboarding_completed"]

    await db.commit()
    await db.refresh(current_user)

    identities = await get_user_identities(db, current_user)
    linked = sorted({i.provider for i in identities})

    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_anonymous=current_user.is_anonymous,
        is_admin=current_user.is_admin,
        email_verified=current_user.email_verified,
        sub_type=current_user.sub_type,
        linked_providers=linked,
        profile=UserProfileResponse(
            about_me=current_user.self_description,
            onboarding_completed=current_user.onboarding_completed,
        ),
    )


class UserMemoryResponse(BaseModel):
    version: int
    updated_at: str
    content_md: str = Field(default="")


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


@router.post("/me/password", response_model=dict)
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """Сменить пароль текущего пользователя."""
    if current_user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account has no password (OAuth-only)",
        )

    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    current_user.password_hash = get_password_hash(data.new_password)
    await db.commit()
    return {"message": "Password updated"}


@router.get("/me/memory", response_model=UserMemoryResponse)
async def get_my_memory(current_user: CurrentUser, db: DatabaseSession):
    """Debug endpoint: view current user.md memory document."""
    doc = await user_memory_service.get_or_create(db, current_user.id)
    return UserMemoryResponse(
        version=doc.version,
        updated_at=doc.updated_at.isoformat() if doc.updated_at else "",
        content_md=doc.content_md or "",
    )
