"""Serve the SDE specification."""
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, JSONResponse

router = APIRouter()
_SPEC_PATH = Path(__file__).parent.parent.parent / "spec" / "SDE-SPEC-v1.md"


@router.get("/spec", tags=["system"])
async def get_spec():
    """Return the SDE specification as Markdown."""
    if _SPEC_PATH.exists():
        return PlainTextResponse(_SPEC_PATH.read_text(encoding="utf-8"), media_type="text/markdown")
    return PlainTextResponse("Spec not found", status_code=404)
