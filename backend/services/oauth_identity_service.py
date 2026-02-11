"""Service for OAuth identity linking."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import OAuthIdentity, User


async def get_identity(
    db: AsyncSession,
    provider: str,
    provider_subject: str,
) -> OAuthIdentity | None:
    result = await db.execute(
        select(OAuthIdentity).where(
            OAuthIdentity.provider == provider,
            OAuthIdentity.provider_subject == provider_subject,
        )
    )
    return result.scalar_one_or_none()


async def get_user_identities(db: AsyncSession, user: User) -> list[OAuthIdentity]:
    result = await db.execute(
        select(OAuthIdentity).where(OAuthIdentity.user_id == user.id)
    )
    return list(result.scalars().all())


async def create_identity(
    db: AsyncSession,
    user: User,
    provider: str,
    provider_subject: str,
    email: str | None,
) -> OAuthIdentity:
    identity = OAuthIdentity(
        user_id=user.id,
        provider=provider,
        provider_subject=provider_subject,
        email=email,
    )
    db.add(identity)
    await db.commit()
    await db.refresh(identity)
    return identity
