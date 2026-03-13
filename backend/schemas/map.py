"""Schemas for dream map API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DreamMapNodeResponse(BaseModel):
    id: str
    symbol_name: str
    display_label: str
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    z: float = Field(ge=-1.0, le=1.0)
    cluster_id: int
    cluster_label: str
    archetype_color: str
    cosine_sim_to_center: float = Field(ge=0.0, le=1.0)
    size_weight: float = Field(ge=0.0, le=1.0)
    occurrence_count: int = Field(ge=1)
    dream_count: int = Field(ge=1)
    last_seen_at: str
    preview_text: str
    related_archetypes: list[str]


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
    min_nodes_required: int


class DreamMapResponse(BaseModel):
    nodes: list[DreamMapNodeResponse]
    clusters: list[DreamMapClusterResponse]
    archetype_filters: list[str]
    meta: DreamMapMetaResponse


class DreamMapOccurrenceResponse(BaseModel):
    dream_id: str
    date: str
    text_preview: str


class DreamMapSymbolDetailResponse(BaseModel):
    id: str
    symbol_name: str
    display_label: str
    primary_dream_id: str
    cluster_id: int
    cluster_label: str
    archetype_color: str
    occurrence_count: int = Field(ge=1)
    dream_count: int = Field(ge=1)
    z: float = Field(ge=-1.0, le=1.0)
    size_weight: float = Field(ge=0.0, le=1.0)
    last_seen_at: str
    related_archetypes: list[str]
    related_symbols: list[str]
    occurrences: list[DreamMapOccurrenceResponse]
