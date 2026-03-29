"""API эндпоинты для пользователя"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from dependencies import CurrentUser, DatabaseSession
from schemas import UserMeResponse, UserProfileResponse, UserSettingsUpdate
from services.oauth_identity_service import get_user_identities
from services import user_memory_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: CurrentUser, db: DatabaseSession):
    identities = await get_user_identities(db, current_user)
    linked = sorted({i.provider for i in identities})

    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        is_anonymous=current_user.is_anonymous,
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
        is_anonymous=current_user.is_anonymous,
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


@router.get("/me/memory", response_model=UserMemoryResponse)
async def get_my_memory(current_user: CurrentUser, db: DatabaseSession):
    """Debug endpoint: view current user.md memory document."""
    doc = await user_memory_service.get_or_create(db, current_user.id)
    return UserMemoryResponse(
        version=doc.version,
        updated_at=doc.updated_at.isoformat() if doc.updated_at else "",
        content_md=doc.content_md or "",
    )
