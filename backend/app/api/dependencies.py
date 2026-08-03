from __future__ import annotations

from fastapi import HTTPException, Request, status

from app.repositories.artifacts import ArtifactRepository


def get_repository(request: Request) -> ArtifactRepository:
    repository = getattr(request.app.state, "repository", None)
    if repository is None:
        detail = getattr(
            request.app.state,
            "artifact_error",
            "Analytics artifacts are unavailable. Run `make generate` and restart the API.",
        )
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
    return repository

