from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SignalWatch API",
    version="0.1.0",
    description="RF anomaly monitoring and explanation API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", tags=["system"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "signalwatch-api",
        "version": app.version,
    }

