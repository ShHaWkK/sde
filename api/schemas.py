"""Pydantic schemas for the SDE API."""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal


class DiffOptions(BaseModel):
    chunking_strategy: Literal["sentence", "paragraph", "sliding_window", "auto"] = "auto"
    embedding_model: str = "all-MiniLM-L6-v2"
    explain: bool = False
    language: str = "en"


class DiffRequest(BaseModel):
    version: str = "1.0"
    text_a: str = Field(..., min_length=1, description="Original text")
    text_b: str = Field(..., min_length=1, description="Revised text")
    domain: Literal["default", "legal", "medical", "code", "journalism"] = "default"
    options: DiffOptions = Field(default_factory=DiffOptions)


class ChunkResult(BaseModel):
    id: int
    a: str | None
    b: str | None
    score: float
    verdict: Literal["identical", "semantic_shift", "contradiction", "added", "removed"]
    explanation: str | None
    confidence: float


class DiffMetadata(BaseModel):
    model: str
    processing_ms: int
    chunk_count_a: int
    chunk_count_b: int


class DiffResponse(BaseModel):
    sde_version: str = "1.0"
    overall: Literal["identical", "semantic_shift", "contradiction", "unrelated"]
    global_score: float = Field(..., ge=0.0, le=1.0)
    delta_index: float = Field(..., ge=0.0, le=1.0)
    chunks: list[ChunkResult]
    metadata: DiffMetadata


class BatchItem(BaseModel):
    id: str | int | None = None
    text_a: str
    text_b: str
    domain: str = "default"
    options: DiffOptions = Field(default_factory=DiffOptions)


class BatchRequest(BaseModel):
    items: list[BatchItem]


class BatchResultItem(BaseModel):
    id: str | int | None
    result: DiffResponse | None
    error: str | None = None


class BatchResponse(BaseModel):
    results: list[BatchResultItem]
    total: int
    failed: int
