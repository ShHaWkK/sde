"""Batch diff endpoint."""
from __future__ import annotations
import asyncio
from fastapi import APIRouter
from api.schemas import BatchRequest, BatchResponse, BatchResultItem, DiffResponse, ChunkResult, DiffMetadata
from core.comparator import SemanticComparator

router = APIRouter()
_comparators: dict[str, SemanticComparator] = {}


def _get_comparator(model_name: str) -> SemanticComparator:
    if model_name not in _comparators:
        _comparators[model_name] = SemanticComparator(model_name=model_name)
    return _comparators[model_name]


@router.post("/batch", response_model=BatchResponse, tags=["batch"])
async def batch_diff(request: BatchRequest):
    """Compare multiple pairs of texts in one request."""
    results: list[BatchResultItem] = []
    failed = 0

    async def process_item(item):
        try:
            comparator = _get_comparator(item.options.embedding_model)
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: comparator.diff(
                    item.text_a,
                    item.text_b,
                    domain=item.domain,
                    chunking_strategy=item.options.chunking_strategy,
                    explain=item.options.explain,
                ),
            )
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
            response = DiffResponse(
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
            return BatchResultItem(id=item.id, result=response)
        except Exception as e:
            return BatchResultItem(id=item.id, result=None, error=str(e))

    tasks = [process_item(item) for item in request.items]
    results = await asyncio.gather(*tasks)

    failed = sum(1 for r in results if r.error)
    return BatchResponse(results=list(results), total=len(results), failed=failed)
