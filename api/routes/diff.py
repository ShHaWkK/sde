"""Diff endpoints."""
from __future__ import annotations
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from api.schemas import DiffRequest, DiffResponse, ChunkResult, DiffMetadata
from core.comparator import SemanticComparator
from core.models import get_embedder

router = APIRouter()

# Module-level comparator cache keyed by model name
_comparators: dict[str, SemanticComparator] = {}


def _get_comparator(model_name: str) -> SemanticComparator:
    if model_name not in _comparators:
        _comparators[model_name] = SemanticComparator(model_name=model_name)
    return _comparators[model_name]


def _build_response(result, request: DiffRequest) -> DiffResponse:
    chunks = [
        ChunkResult(
            id=p.id,
            a=p.text_a,
            b=p.text_b,
            score=p.score,
            verdict=p.verdict,
            explanation=p.explanation,
            confidence=p.confidence,
        )
        for p in result.chunks
    ]
    return DiffResponse(
        sde_version=result.sde_version,
        overall=result.overall,
        global_score=result.global_score,
        delta_index=result.delta_index,
        chunks=chunks,
        metadata=DiffMetadata(
            model=result.model,
            processing_ms=result.processing_ms,
            chunk_count_a=result.chunk_count_a,
            chunk_count_b=result.chunk_count_b,
        ),
    )


@router.post("/diff", response_model=DiffResponse, tags=["diff"])
async def diff(request: DiffRequest):
    """Compare two texts semantically."""
    try:
        comparator = _get_comparator(request.options.embedding_model)
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: comparator.diff(
                request.text_a,
                request.text_b,
                domain=request.domain,
                chunking_strategy=request.options.chunking_strategy,
                explain=request.options.explain,
            ),
        )
        return _build_response(result, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/diff/stream", tags=["diff"])
async def diff_stream(request: DiffRequest):
    """Stream chunk results as they are computed (Server-Sent Events)."""

    async def generate():
        try:
            comparator = _get_comparator(request.options.embedding_model)
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: comparator.diff(
                    request.text_a,
                    request.text_b,
                    domain=request.domain,
                    chunking_strategy=request.options.chunking_strategy,
                    explain=request.options.explain,
                ),
            )
            for chunk in result.chunks:
                data = ChunkResult(
                    id=chunk.id,
                    a=chunk.text_a,
                    b=chunk.text_b,
                    score=chunk.score,
                    verdict=chunk.verdict,
                    explanation=chunk.explanation,
                    confidence=chunk.confidence,
                )
                yield f"data: {data.model_dump_json()}\n\n"
            # Final summary event
            summary = {
                "event": "done",
                "overall": result.overall,
                "global_score": result.global_score,
                "delta_index": result.delta_index,
            }
            yield f"data: {json.dumps(summary)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
