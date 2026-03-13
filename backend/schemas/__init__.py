"""Pydantic схемы"""

from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserSettingsUpdate,
    UserResponse,
    UserPublic,
    UserProfileResponse,
    UserMeResponse,
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
from .analysis_message import (
    MessageSend,
    ChatMessageResponse,
    ChatMessageListResponse,
    ChatMessageTaskResponse,
)
from .audio import TranscriptionResponse
from .map import (
    DreamMapClusterCenter,
    DreamMapClusterResponse,
    DreamMapMetaResponse,
    DreamMapNodeResponse,
    DreamMapOccurrenceResponse,
    DreamMapResponse,
    DreamMapSymbolDetailResponse,
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
    AnonymousAuthRequest,
    AnonymousAuthResponse,
    LinkRequest,
    LinkResponse,
    AuthUserResponse,
    ProviderIdentityResponse,
)
from .stats import StatsResponse

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserSettingsUpdate",
    "UserResponse",
    "UserPublic",
    "UserProfileResponse",
    "UserMeResponse",
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
    # Analysis Messages
    "MessageSend",
    "ChatMessageResponse",
    "ChatMessageListResponse",
    "ChatMessageTaskResponse",
    "TranscriptionResponse",
    "DreamMapClusterCenter",
    "DreamMapClusterResponse",
    "DreamMapMetaResponse",
    "DreamMapNodeResponse",
    "DreamMapOccurrenceResponse",
    "DreamMapResponse",
    "DreamMapSymbolDetailResponse",
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
    "AnonymousAuthRequest",
    "AnonymousAuthResponse",
    "LinkRequest",
    "LinkResponse",
    "AuthUserResponse",
    "ProviderIdentityResponse",
    "StatsResponse",
]
