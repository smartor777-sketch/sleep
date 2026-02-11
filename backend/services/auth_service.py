"""Сервис для аутентификации"""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, EmailVerification, PasswordReset
from schemas import UserCreate

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверить пароль
    
    Args:
        plain_password: Обычный пароль
        hashed_password: Хешированный пароль
    
    Returns:
        True если пароли совпадают
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Хешировать пароль
    
    Args:
        password: Обычный пароль
    
    Returns:
        Хешированный пароль
    """
    return pwd_context.hash(password)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
    Получить пользователя по email
    
    Args:
        db: Сессия базы данных
        email: Email пользователя
    
    Returns:
        Пользователь или None
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Создать нового пользователя
    
    Args:
        db: Сессия базы данных
        user_data: Данные пользователя
    
    Returns:
        Созданный пользователь
    """
    hashed_password = get_password_hash(user_data.password)
    
    user = User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        timezone=user_data.timezone,
        is_anonymous=False,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


async def get_user_by_device_id(db: AsyncSession, device_id: str) -> User | None:
    """Получить пользователя по device_id"""
    result = await db.execute(
        select(User).where(User.device_id == device_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_anonymous_user(
    db: AsyncSession,
    device_id: str,
) -> tuple[User, bool]:
    """
    Получить или создать анонимного пользователя по device_id.

    Returns:
        (user, is_new)
    """
    existing = await get_user_by_device_id(db, device_id)
    if existing:
        return existing, False

    user = User(
        email=None,
        password_hash=None,
        first_name=None,
        last_name=None,
        timezone="UTC",
        is_anonymous=True,
        device_id=device_id,
        email_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, True


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """
    Аутентифицировать пользователя
    
    Args:
        db: Сессия базы данных
        email: Email пользователя
        password: Пароль
    
    Returns:
        Пользователь или None если аутентификация не удалась
    """
    user = await get_user_by_email(db, email)
    
    if not user:
        return None
    
    if not user.password_hash:
        # Пользователь зарегистрирован через OAuth2
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return user


async def create_email_verification_token(
    db: AsyncSession,
    user_id: UUID,
    expires_hours: int = 24
) -> str:
    """
    Создать токен для подтверждения email
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        expires_hours: Время жизни токена в часах
    
    Returns:
        Токен
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    
    verification = EmailVerification(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    
    db.add(verification)
    await db.commit()
    
    return token


async def verify_email_token(db: AsyncSession, token: str) -> User | None:
    """
    Верифицировать email по токену
    
    Args:
        db: Сессия базы данных
        token: Токен верификации
    
    Returns:
        Пользователь или None если токен невалиден
    """
    result = await db.execute(
        select(EmailVerification).where(EmailVerification.token == token)
    )
    verification = result.scalar_one_or_none()
    
    if not verification:
        return None
    
    if verification.expires_at < datetime.now(timezone.utc):
        # Токен истёк
        await db.delete(verification)
        await db.commit()
        return None
    
    # Получаем пользователя
    result = await db.execute(
        select(User).where(User.id == verification.user_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Подтверждаем email
        user.email_verified = True
        await db.delete(verification)
        await db.commit()
        await db.refresh(user)
    
    return user


async def create_password_reset_token(
    db: AsyncSession,
    user_id: UUID,
    expires_hours: int = 1
) -> str:
    """
    Создать токен для сброса пароля
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        expires_hours: Время жизни токена в часах
    
    Returns:
        Токен
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    
    reset = PasswordReset(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    
    db.add(reset)
    await db.commit()
    
    return token


async def reset_password(db: AsyncSession, token: str, new_password: str) -> User | None:
    """
    Сбросить пароль по токену
    
    Args:
        db: Сессия базы данных
        token: Токен сброса пароля
        new_password: Новый пароль
    
    Returns:
        Пользователь или None если токен невалиден
    """
    result = await db.execute(
        select(PasswordReset).where(
            PasswordReset.token == token,
            PasswordReset.used == False
        )
    )
    reset = result.scalar_one_or_none()
    
    if not reset:
        return None
    
    if reset.expires_at < datetime.now(timezone.utc):
        # Токен истёк
        await db.delete(reset)
        await db.commit()
        return None
    
    # Получаем пользователя
    result = await db.execute(
        select(User).where(User.id == reset.user_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Обновляем пароль
        user.password_hash = get_password_hash(new_password)
        reset.used = True
        await db.commit()
        await db.refresh(user)
    
    return user
