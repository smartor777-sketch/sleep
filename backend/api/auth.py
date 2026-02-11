"""API эндпоинты для аутентификации"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, Query

from dependencies import (
    DatabaseSession,
    CurrentUser,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ResendVerificationRequest,
    MessageResponse,
    AnonymousAuthRequest,
    AnonymousAuthResponse,
    AuthUserResponse,
    LinkRequest,
    LinkResponse,
    ProviderIdentityResponse,
)
from services.auth_service import (
    get_user_by_email,
    create_user,
    authenticate_user,
    create_email_verification_token,
    verify_email_token,
    create_password_reset_token,
    reset_password,
    get_or_create_anonymous_user,
)
from services.email_service import email_service
from services.oauth_token_service import verify_google_id_token, verify_apple_id_token
from services.oauth_identity_service import (
    get_identity,
    get_user_identities,
    create_identity,
)
from models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    db: DatabaseSession
):
    """
    Регистрация нового пользователя
    
    - Проверяет, что email не занят
    - Создаёт пользователя с хешированным паролем
    - Отправляет письмо для подтверждения email
    - Возвращает JWT токены
    """
    # Проверяем, что email не занят
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Создаём пользователя
    try:
        user = await create_user(db, user_data)
        logger.info(f"New user registered: {user.email}")
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    # Создаём токен для подтверждения email
    try:
        verification_token = await create_email_verification_token(db, user.id)
        email_service.send_verification_email(user.email, verification_token)
        logger.info(f"Verification email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        # Не прерываем регистрацию, если email не отправился
    
    # Создаём JWT токены
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: DatabaseSession
):
    """
    Вход в систему
    
    - Проверяет email и пароль
    - Возвращает JWT токены
    """
    user = await authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )
    
    # Создаём JWT токены
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    logger.info(f"User logged in: {user.email}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/anonymous", response_model=AnonymousAuthResponse)
async def anonymous_auth(
    data: AnonymousAuthRequest,
    db: DatabaseSession,
):
    """
    Анонимная авторизация по device_id.

    - Если device_id существует -> выдаём токены
    - Если нет -> создаём пользователя и выдаём токены
    """
    if not data.device_id or len(data.device_id) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid device_id"
        )

    try:
        user, _ = await get_or_create_anonymous_user(db, data.device_id)

        # Обновляем last_login_at
        user.last_login_at = datetime.utcnow()
        await db.commit()

        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return AnonymousAuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=AuthUserResponse(
                id=str(user.id),
                is_anonymous=user.is_anonymous,
                email=user.email,
            ),
        )
    except Exception as e:
        logger.error(f"Failed anonymous auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed anonymous auth"
        )


@router.post("/link", response_model=LinkResponse)
async def link_provider(
    data: LinkRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """
    Привязка Google/Apple к текущему пользователю.
    """
    provider = data.provider.lower().strip()
    if provider not in {"google", "apple"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_provider"
        )

    try:
        if provider == "google":
            claims = await verify_google_id_token(data.id_token)
        else:
            claims = await verify_apple_id_token(data.id_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    provider_subject = claims.get("sub")
    email = claims.get("email")

    # Проверяем, не привязан ли identity к другому пользователю
    existing = await get_identity(db, provider, provider_subject)
    if existing and existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="identity_already_linked"
        )

    # Проверяем, нет ли уже identity этого provider у пользователя
    user_identities = await get_user_identities(db, current_user)
    if any(i.provider == provider for i in user_identities) and not existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="user_already_has_identity"
        )

    if existing and existing.user_id == current_user.id:
        identity = existing
    else:
        identity = await create_identity(db, current_user, provider, provider_subject, email)

    # Обновляем пользователя
    if current_user.is_anonymous:
        current_user.is_anonymous = False
    if not current_user.email and email:
        current_user.email = email
    await db.commit()

    return LinkResponse(
        linked=True,
        user=AuthUserResponse(
            id=str(current_user.id),
            is_anonymous=current_user.is_anonymous,
            email=current_user.email,
        ),
        provider_identity=ProviderIdentityResponse(
            provider=identity.provider,
            provider_subject=identity.provider_subject,
            email=identity.email,
        ),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    refresh_data: RefreshTokenRequest,
    db: DatabaseSession
):
    """
    Обновить access token используя refresh token
    """
    try:
        payload = verify_token(refresh_data.refresh_token, token_type="refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Создаём новые токены
        access_token = create_access_token(data={"sub": user_id})
        new_refresh_token = create_refresh_token(data={"sub": user_id})
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/verify-email", response_model=MessageResponse)
async def verify_email(
    db: DatabaseSession,
    token: str = Query(..., description="Verification token"),
):
    """
    Подтвердить email по токену
    """
    user = await verify_email_token(db, token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    logger.info(f"Email verified for user: {user.email}")
    
    return {"message": "Email successfully verified"}


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    request: ResendVerificationRequest,
    db: DatabaseSession
):
    """
    Повторная отправка письма подтверждения email
    """
    user = await get_user_by_email(db, request.email)
    
    if not user:
        # Не раскрываем, что пользователь не существует (security)
        return {"message": "If the email exists, verification email has been sent"}
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Создаём новый токен
    verification_token = await create_email_verification_token(db, user.id)
    
    try:
        email_service.send_verification_email(user.email, verification_token)
        logger.info(f"Verification email resent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
    
    return {"message": "Verification email has been sent"}


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: DatabaseSession
):
    """
    Запрос восстановления пароля
    """
    user = await get_user_by_email(db, request.email)
    
    if not user:
        # Не раскрываем, что пользователь не существует (security)
        return {"message": "If the email exists, password reset email has been sent"}
    
    if not user.password_hash:
        # Пользователь зарегистрирован через OAuth2
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reset password for OAuth2 accounts"
        )
    
    # Создаём токен для сброса пароля
    reset_token = await create_password_reset_token(db, user.id)
    
    try:
        email_service.send_password_reset_email(user.email, reset_token)
        logger.info(f"Password reset email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email"
        )
    
    return {"message": "Password reset email has been sent"}


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password_endpoint(
    request: ResetPasswordRequest,
    db: DatabaseSession
):
    """
    Сброс пароля по токену
    """
    user = await reset_password(db, request.token, request.new_password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    logger.info(f"Password reset for user: {user.email}")
    
    return {"message": "Password successfully reset"}


@router.delete("/account", response_model=MessageResponse)
async def delete_account(
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    Удалить аккаунт текущего пользователя
    
    - Удаляет пользователя и все связанные данные (каскадно)
    """
    try:
        await db.delete(current_user)
        await db.commit()
        logger.info(f"Account deleted: {current_user.email}")
        
        return {"message": "Account successfully deleted"}
    
    except Exception as e:
        logger.error(f"Failed to delete account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout():
    """
    Выход из системы
    
    В текущей реализации JWT токены stateless, 
    поэтому нужно удалять токены на клиенте.
    
    В будущем можно добавить blacklist для токенов в Redis.
    """
    return {"message": "Successfully logged out"}
