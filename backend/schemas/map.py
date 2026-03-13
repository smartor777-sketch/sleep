"""Schemas for dream map API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DreamMapNodeResponse(BaseModel):
    id: str
    dream_id: str
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    z: float = Field(ge=-1.0, le=1.0)
    cluster_id: int
    cluster_label: str
    archetype_color: str
    cosine_sim_to_center: float = Field(ge=0.0, le=1.0)
    size_weight: float = Field(ge=0.0, le=1.0)
    text_preview: str
    date: str
    emotion_valence: float = Field(ge=-1.0, le=1.0)
    tokens: int


class DreamMapClusterCenter(BaseModel):
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)


class DreamMapClusterResponse(BaseModel):
    id: int
    label: str
    color: str
    count: int
    center: DreamMapClusterCenter


class DreamMapMetaResponse(BaseModel):
    total_nodes: int
    total_clusters: int
    cached: bool
    computed_with: str
    cluster_method: str
    min_chunks_required: int


class DreamMapResponse(BaseModel):
    nodes: list[DreamMapNodeResponse]
    clusters: list[DreamMapClusterResponse]
    meta: DreamMapMetaResponse


class DreamMapNeighborResponse(BaseModel):
    chunk_id: str
    dream_id: str
    text_preview: str
    cosine_similarity: float = Field(ge=0.0, le=1.0)
    date: str


class DreamMapChunkDetailResponse(BaseModel):
    id: str
    dream_id: str
    cluster_id: int
    cluster_label: str
    archetype_color: str
    text: str
    date: str
    emotion_valence: float = Field(ge=-1.0, le=1.0)
    tokens: int
    z: float = Field(ge=-1.0, le=1.0)
    size_weight: float = Field(ge=0.0, le=1.0)
    neighbors: list[DreamMapNeighborResponse]
