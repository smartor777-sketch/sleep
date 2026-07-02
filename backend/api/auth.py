"""API эндпоинты для аутентификации"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends, Query, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from dependencies import (
    DatabaseSession,
    CurrentUser,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from uuid import UUID

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
    VerifyEmailCodeRequest,
    MergeAnonymousRequest,
    GoogleSignInRequest,
    TelegramInitResponse,
    TelegramStatusResponse,
    TelegramConfirmRequest,
    YandexInitResponse,
    YandexExchangeRequest,
    YandexExchangeResponse,
    YandexStatusResponse,
    VkInitResponse,
    VkExchangeRequest,
    VkExchangeResponse,
    VkStatusResponse,
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
    create_email_verification_code,
    verify_email_code,
    merge_anonymous_user,
)
from services.email_service import email_service
from services import telegram_auth_service as tg_auth
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
    
    # Генерируем 6-значный код подтверждения (логируем для dev-тестирования)
    try:
        await create_email_verification_code(db, user.id)
    except Exception as e:
        logger.error(f"Failed to create verification code: {e}")
        # Не прерываем регистрацию

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
        user, is_new = await get_or_create_anonymous_user(db, data.device_id)

        if is_new:
            from services.billing_service import start_trial
            start_trial(user)

        # Обновляем last_login_at
        user.last_login_at = datetime.now(timezone.utc)
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


@router.post("/verify-email-code", response_model=MessageResponse)
async def verify_email_code_endpoint(
    request: VerifyEmailCodeRequest,
    db: DatabaseSession,
):
    """Подтвердить email по 6-значному коду."""
    user = await verify_email_code(db, request.email, request.code)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_or_expired_code",
        )
    logger.info(f"Email verified via code for user: {user.email}")
    return {"message": "Email verified"}


@router.post("/resend-code", response_model=MessageResponse)
async def resend_code_endpoint(
    request: ResendVerificationRequest,
    db: DatabaseSession,
):
    """Переслать 6-значный код подтверждения email."""
    user = await get_user_by_email(db, request.email)
    if not user:
        return {"message": "If the email exists, a code has been sent"}
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email_already_verified",
        )
    await create_email_verification_code(db, user.id)
    return {"message": "Code sent"}


_optional_bearer = HTTPBearer(auto_error=False)


@router.post("/google", response_model=TokenResponse)
async def google_signin(
    data: GoogleSignInRequest,
    db: DatabaseSession,
    credentials: HTTPAuthorizationCredentials | None = Security(_optional_bearer),
):
    """
    Google Sign-In.

    - Если Google-аккаунт уже привязан → возвращает токены существующего пользователя.
    - Если нет → привязывает к текущему анонимному (по JWT в заголовке) или создаёт нового.
    """
    try:
        claims = await verify_google_id_token(data.id_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    provider_subject = claims["sub"]
    email = claims.get("email")

    # Проверяем, есть ли уже привязанный аккаунт с этим Google ID
    existing_identity = await get_identity(db, "google", provider_subject)
    if existing_identity:
        from sqlalchemy import select as sa_select
        from models import User as UserModel
        result = await db.execute(sa_select(UserModel).where(UserModel.id == existing_identity.user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_not_found")
        logger.info(f"Google Sign-In: existing user {user.id}")
    else:
        # Пытаемся получить текущего анонимного пользователя из JWT
        user = None
        if credentials:
            try:
                payload = verify_token(credentials.credentials, token_type="access")
                uid = payload.get("sub")
                if uid:
                    from sqlalchemy import select as sa_select
                    from models import User as UserModel
                    result = await db.execute(sa_select(UserModel).where(UserModel.id == UUID(uid)))
                    user = result.scalar_one_or_none()
            except Exception:
                pass

        if user is None:
            user = User(
                email=email,
                is_anonymous=False,
                email_verified=bool(email),
                timezone="UTC",
            )
            from services.billing_service import start_trial
            start_trial(user)
            db.add(user)
            await db.commit()
            await db.refresh(user)

        await create_identity(db, user, "google", provider_subject, email)
        if user.is_anonymous:
            user.is_anonymous = False
            # Anon → first registered identity. Give them the trial too.
            from services.billing_service import start_trial
            start_trial(user)
        if not user.email and email:
            user.email = email
            user.email_verified = True
        await db.commit()
        logger.info(f"Google Sign-In: linked new Google identity to user {user.id}")

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/merge-anonymous", response_model=MessageResponse)
async def merge_anonymous_endpoint(
    request: MergeAnonymousRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """Перенести данные из анонимного аккаунта в текущий зарегистрированный."""
    merged = await merge_anonymous_user(db, current_user, request.anonymous_device_id)
    if not merged:
        # Не бросаем ошибку — возможно, анонимный аккаунт уже удалён
        return {"message": "No anonymous account found"}
    return {"message": "Anonymous data merged"}


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


# === Telegram bot deep-link auth ===

from fastapi import Header
from config import settings


def _bot_username_or_500() -> str:
    if not settings.telegram_bot_username:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="telegram_auth_not_configured",
        )
    return settings.telegram_bot_username


def _bot_secret_or_500() -> str:
    if not settings.telegram_bot_backend_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="telegram_auth_not_configured",
        )
    return settings.telegram_bot_backend_secret.get_secret_value()


async def _verify_bot_caller(authorization: str = Header(...)) -> None:
    expected = _bot_secret_or_500()
    if authorization != f"Bot {expected}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_bot_secret",
        )


@router.post("/telegram/init", response_model=TelegramInitResponse)
async def telegram_init() -> TelegramInitResponse:
    """Web → backend: дай мне токен и deeplink на бота."""
    bot_username = _bot_username_or_500()
    token = await tg_auth.create_pending_token()
    return TelegramInitResponse(
        auth_token=token,
        deeplink=f"https://t.me/{bot_username}?start={token}",
        bot_username=bot_username,
        expires_in=tg_auth.TOKEN_TTL_SECONDS,
    )


@router.get("/telegram/status", response_model=TelegramStatusResponse)
async def telegram_status(auth_token: str = Query(..., min_length=10, max_length=128)) -> TelegramStatusResponse:
    """Web поллит статус. Один-shot: при completed — отдаём токены и удаляем."""
    state = await tg_auth.get_token_state(auth_token)
    if state is None:
        return TelegramStatusResponse(status="expired")
    if state.get("status") == "pending":
        return TelegramStatusResponse(status="pending")
    return TelegramStatusResponse(
        status="completed",
        access_token=state.get("access_token"),
        refresh_token=state.get("refresh_token"),
        token_type=state.get("token_type", "bearer"),
    )


@router.post(
    "/telegram/confirm",
    response_model=MessageResponse,
    dependencies=[Depends(_verify_bot_caller)],
)
async def telegram_confirm(
    body: TelegramConfirmRequest,
    db: DatabaseSession,
) -> MessageResponse:
    """Бот → backend: пользователь нажал /start <auth_token>. Создаём/находим юзера, сохраняем JWT в Redis под токеном."""
    # Make sure the auth_token is still alive (don't consume it here — that happens in complete_token).
    from services.telegram_auth_service import _redis as _tg_redis, KEY_PREFIX as _KP
    client = await _tg_redis()
    try:
        exists = await client.exists(_KP + body.auth_token)
    finally:
        await client.close()
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="auth_token_expired",
        )

    user = await tg_auth.get_or_create_telegram_user(
        db,
        telegram_id=body.telegram_id,
        username=body.username,
        first_name=body.first_name,
        last_name=body.last_name,
    )

    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})

    ok = await tg_auth.complete_token(body.auth_token, access, refresh)
    if not ok:
        # token expired between exists() and complete_token — extremely unlikely
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="auth_token_expired",
        )

    logger.info("Telegram auth completed for user=%s telegram_id=%s", user.id, body.telegram_id)
    return {"message": "ok"}


# === Yandex OAuth ===

import services.yandex_auth_service as yandex_auth


@router.post("/yandex/init", response_model=YandexInitResponse)
async def yandex_init() -> YandexInitResponse:
    """Шаг 1: создать state-токен и вернуть URL на Яндекс."""
    try:
        state = await yandex_auth.create_state()
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    return YandexInitResponse(
        state=state,
        auth_url=yandex_auth.build_auth_url(state),
        expires_in=yandex_auth.STATE_TTL,
    )


@router.post("/yandex/exchange", response_model=YandexExchangeResponse)
async def yandex_exchange(
    data: YandexExchangeRequest,
    db: DatabaseSession,
    credentials: HTTPAuthorizationCredentials | None = Security(_optional_bearer),
) -> YandexExchangeResponse:
    """
    Шаг 2: callback-страница обменивает code на JWT.
    Также сохраняет результат в Redis под state — мобильный клиент подтянет через /status.
    """
    state_data = await yandex_auth.get_state_data(data.state)
    if state_data is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="yandex_state_expired")
    if state_data.get("status") == "completed":
        return YandexExchangeResponse(
            access_token=state_data["access_token"],
            refresh_token=state_data["refresh_token"],
        )

    try:
        token_data = await yandex_auth.exchange_code(data.code)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    yandex_access_token = token_data.get("access_token")
    if not yandex_access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="yandex_no_access_token")

    try:
        user_info = await yandex_auth.get_user_info(yandex_access_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    provider_subject = str(user_info.get("id") or user_info.get("client_id") or "")
    if not provider_subject:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="yandex_no_user_id")

    email = user_info.get("default_email") or user_info.get("emails", [None])[0]

    existing_identity = await get_identity(db, "yandex", provider_subject)
    if existing_identity:
        from sqlalchemy import select as sa_select
        from models import User as UserModel
        result = await db.execute(sa_select(UserModel).where(UserModel.id == existing_identity.user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_not_found")
    else:
        # Попробуем привязать к текущему анонимному пользователю если есть JWT
        user = None
        if credentials:
            try:
                payload = verify_token(credentials.credentials, token_type="access")
                uid = payload.get("sub")
                if uid:
                    from sqlalchemy import select as sa_select
                    from models import User as UserModel
                    result = await db.execute(sa_select(UserModel).where(UserModel.id == UUID(uid)))
                    user = result.scalar_one_or_none()
            except Exception:
                pass

        if user is None:
            from models import User as UserModel
            user = UserModel(
                email=email,
                is_anonymous=False,
                email_verified=bool(email),
                timezone="UTC",
            )
            from services.billing_service import start_trial
            start_trial(user)
            db.add(user)
            await db.commit()
            await db.refresh(user)

        await create_identity(db, user, "yandex", provider_subject, email)
        if user.is_anonymous:
            user.is_anonymous = False
            from services.billing_service import start_trial
            start_trial(user)
        if not user.email and email:
            user.email = email
            user.email_verified = True
        await db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    await yandex_auth.complete_state(data.state, access_token, refresh_token)
    logger.info("Yandex auth completed for user=%s", user.id)

    return YandexExchangeResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/yandex/status", response_model=YandexStatusResponse)
async def yandex_status(state: str = Query(..., min_length=10, max_length=64)) -> YandexStatusResponse:
    """Мобильный клиент поллит этот эндпоинт пока callback-страница не завершит обмен."""
    data = await yandex_auth.get_state_data(state)
    if data is None:
        return YandexStatusResponse(status="expired")
    if data.get("status") == "completed":
        return YandexStatusResponse(
            status="completed",
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "bearer"),
        )
    return YandexStatusResponse(status="pending")


# === VK ID OAuth ===

import services.vk_auth_service as vk_auth


@router.post("/vk/init", response_model=VkInitResponse)
async def vk_init() -> VkInitResponse:
    try:
        state = await vk_auth.create_state()
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    return VkInitResponse(
        state=state,
        auth_url=vk_auth.build_auth_url(state),
        expires_in=vk_auth.STATE_TTL,
    )


@router.post("/vk/exchange", response_model=VkExchangeResponse)
async def vk_exchange(
    data: VkExchangeRequest,
    db: DatabaseSession,
    credentials: HTTPAuthorizationCredentials | None = Security(_optional_bearer),
) -> VkExchangeResponse:
    state_data = await vk_auth.get_state_data(data.state)
    if state_data is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="vk_state_expired")
    if state_data.get("status") == "completed":
        return VkExchangeResponse(
            access_token=state_data["access_token"],
            refresh_token=state_data["refresh_token"],
        )

    try:
        token_data = await vk_auth.exchange_code(data.code)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    provider_subject = str(token_data.get("user_id", ""))
    if not provider_subject:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="vk_no_user_id")

    email = token_data.get("email")  # VK returns email in token response if scope=email granted

    existing_identity = await get_identity(db, "vk", provider_subject)
    if existing_identity:
        from sqlalchemy import select as sa_select
        from models import User as UserModel
        result = await db.execute(sa_select(UserModel).where(UserModel.id == existing_identity.user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_not_found")
    else:
        user = None
        if credentials:
            try:
                payload = verify_token(credentials.credentials, token_type="access")
                uid = payload.get("sub")
                if uid:
                    from sqlalchemy import select as sa_select
                    from models import User as UserModel
                    result = await db.execute(sa_select(UserModel).where(UserModel.id == UUID(uid)))
                    user = result.scalar_one_or_none()
            except Exception:
                pass

        if user is None:
            from models import User as UserModel
            user = UserModel(
                email=email,
                is_anonymous=False,
                email_verified=bool(email),
                timezone="UTC",
            )
            from services.billing_service import start_trial
            start_trial(user)
            db.add(user)
            await db.commit()
            await db.refresh(user)

        await create_identity(db, user, "vk", provider_subject, email)
        if user.is_anonymous:
            user.is_anonymous = False
            from services.billing_service import start_trial
            start_trial(user)
        if not user.email and email:
            user.email = email
            user.email_verified = True
        await db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    await vk_auth.complete_state(data.state, access_token, refresh_token)
    logger.info("VK auth completed for user=%s vk_id=%s", user.id, provider_subject)

    return VkExchangeResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/vk/status", response_model=VkStatusResponse)
async def vk_status(state: str = Query(..., min_length=10, max_length=64)) -> VkStatusResponse:
    data = await vk_auth.get_state_data(state)
    if data is None:
        return VkStatusResponse(status="expired")
    if data.get("status") == "completed":
        return VkStatusResponse(
            status="completed",
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "bearer"),
        )
    return VkStatusResponse(status="pending")
