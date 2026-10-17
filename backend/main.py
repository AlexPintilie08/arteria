"""FastAPI entry point for the local ARTERIA backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.settings import settings


app = FastAPI(
    title="ARTERIA API",
    version="0.1.0",
    description="Local API foundation. Urban analysis endpoints are not implemented yet.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Return a lightweight liveness response without requiring external services."""
    return {"status": "ok", "service": "arteria-backend"}
