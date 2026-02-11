"""API эндпоинты для пользователя"""

from fastapi import APIRouter

from dependencies import CurrentUser, DatabaseSession
from schemas import UserMeResponse, UserProfileResponse, UserSettingsUpdate
from services.oauth_identity_service import get_user_identities

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: CurrentUser, db: DatabaseSession):
    identities = await get_user_identities(db, current_user)
    linked = sorted({i.provider for i in identities})

    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        is_anonymous=current_user.is_anonymous,
        linked_providers=linked,
        profile=UserProfileResponse(
            about_me=current_user.self_description,
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

    await db.commit()
    await db.refresh(current_user)

    identities = await get_user_identities(db, current_user)
    linked = sorted({i.provider for i in identities})

    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        is_anonymous=current_user.is_anonymous,
        linked_providers=linked,
        profile=UserProfileResponse(
            about_me=current_user.self_description,
        ),
    )
