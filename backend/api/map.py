"""API endpoints for dream map."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from database import AsyncSessionLocal
from dependencies import CurrentUser, DatabaseSession, verify_token
from models import User
from schemas.map import DreamMapResponse, DreamMapSymbolDetailResponse
from services.map_service import (
    DEFAULT_STREAM_BATCH_SIZE,
    get_dream_map,
    get_map_symbol_detail,
    stream_dream_map,
)

router = APIRouter(prefix="/map", tags=["Map"])


def _ensure_same_user(requested_user_id: UUID, current_user_id: UUID) -> None:
    if requested_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Map access is only available for your own account",
        )


@router.get("/{user_id}", response_model=DreamMapResponse)
async def get_dream_map_endpoint(
    user_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    n_neighbors: int = Query(15, ge=2, le=50),
    min_dist: float = Query(0.02, ge=0.0, le=0.99),
    cluster_method: str = Query("dbscan", pattern="^(dbscan|fallback)$"),
    force_refresh: bool = Query(False),
    dispersion: float = Query(1.0, ge=0.1, le=5.0),
    jitter: float = Query(0.03, ge=0.0, le=0.2),
):
    _ensure_same_user(user_id, current_user.id)
    return await get_dream_map(
        db,
        user_id=user_id,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        cluster_method=cluster_method,
        force_refresh=force_refresh,
        dispersion=dispersion,
        jitter=jitter,
    )


@router.get("/{user_id}/symbol/{symbol_id}", response_model=DreamMapSymbolDetailResponse)
async def get_dream_map_symbol_detail_endpoint(
    user_id: UUID,
    symbol_id: str,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    _ensure_same_user(user_id, current_user.id)
    detail = await get_map_symbol_detail(db, user_id=user_id, symbol_id=symbol_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map symbol not found",
        )
    return detail


@router.websocket("/{user_id}/stream")
async def dream_map_stream_endpoint(
    websocket: WebSocket,
    user_id: UUID,
    n_neighbors: int = Query(15, ge=2, le=50),
    min_dist: float = Query(0.02, ge=0.0, le=0.99),
    cluster_method: str = Query("dbscan", pattern="^(dbscan|fallback)$"),
    force_refresh: bool = Query(False),
    dispersion: float = Query(1.0, ge=0.1, le=5.0),
    jitter: float = Query(0.03, ge=0.0, le=0.2),
):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401, reason="Missing auth token")
        return

    try:
        payload = verify_token(token, token_type="access")
        token_user_id = UUID(payload["sub"])
    except Exception:
        await websocket.close(code=4401, reason="Invalid auth token")
        return

    if token_user_id != user_id:
        await websocket.close(code=4403, reason="Forbidden")
        return

    await websocket.accept()
    try:
        async with AsyncSessionLocal() as db:
            user = (await db.execute(select(User).where(User.id == token_user_id))).scalar_one_or_none()
            if user is None:
                await websocket.close(code=4404, reason="User not found")
                return
            async for message in stream_dream_map(
                db,
                user_id=user_id,
                n_neighbors=n_neighbors,
                min_dist=min_dist,
                cluster_method=cluster_method,
                force_refresh=force_refresh,
                batch_size=DEFAULT_STREAM_BATCH_SIZE,
                dispersion=dispersion,
                jitter=jitter,
            ):
                await websocket.send_text(json.dumps(message))
    except WebSocketDisconnect:
        return
    except Exception as exc:
        await websocket.send_text(json.dumps({"type": "error", "detail": str(exc)}))
        await websocket.close(code=1011)
