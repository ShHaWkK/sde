"""FastAPI application for the Semantic Diff Engine."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import diff, batch, health, spec
from api.middleware.rate_limit import RateLimitMiddleware

app = FastAPI(
    title="Semantic Diff Engine",
    description="The semantic layer missing from your pipeline.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — open for playground / SDK use
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)

app.include_router(health.router)
app.include_router(spec.router)
app.include_router(diff.router)
app.include_router(batch.router)


@app.get("/", tags=["system"])
async def root():
    return {
        "name": "Semantic Diff Engine",
        "version": "1.0.0",
        "spec": "/spec",
        "docs": "/docs",
    }
