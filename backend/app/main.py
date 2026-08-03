from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.repositories.artifacts import ArtifactRepository, ArtifactUnavailableError


@asynccontextmanager
async def lifespan(application: FastAPI):
    data_dir = Path(os.environ.get("SIGNALWATCH_DATA_DIR", "../data")).resolve()
    repository = ArtifactRepository(data_dir)
    try:
        repository.load()
        application.state.repository = repository
        application.state.artifact_error = None
    except ArtifactUnavailableError as error:
        application.state.repository = None
        application.state.artifact_error = str(error)
    yield

app = FastAPI(
    title="SignalWatch API",
    version="0.1.0",
    description="RF anomaly monitoring and explanation API.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/api/v1/health", tags=["system"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "signalwatch-api",
        "version": app.version,
    }
