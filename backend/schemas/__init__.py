"""Pydantic схемы"""

from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserSettingsUpdate,
    UserResponse,
    UserPublic,
)
from .dream import (
    DreamBase,
    DreamCreate,
    DreamUpdate,
    DreamResponse,
    DreamListResponse,
    DreamSearchResponse,
)
from .analysis import (
    AnalysisCreate,
    AnalysisResponse,
    AnalysisTaskResponse,
    AnalysisTaskStatusResponse,
    AnalysisListResponse,
)
from .auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ResendVerificationRequest,
    MessageResponse,
    OAuth2CallbackResponse,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserSettingsUpdate",
    "UserResponse",
    "UserPublic",
    # Dream
    "DreamBase",
    "DreamCreate",
    "DreamUpdate",
    "DreamResponse",
    "DreamListResponse",
    "DreamSearchResponse",
    # Analysis
    "AnalysisCreate",
    "AnalysisResponse",
    "AnalysisTaskResponse",
    "AnalysisTaskStatusResponse",
    "AnalysisListResponse",
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "ResendVerificationRequest",
    "MessageResponse",
    "OAuth2CallbackResponse",
]

