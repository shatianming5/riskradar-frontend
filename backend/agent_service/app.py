from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .graph import analyze
from .schemas import AnalyzeRequest, AnalyzeResponse


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="RiskRadar Agent Service", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "service": "riskradar-agent-service",
            "llm_enabled": settings.llm_enabled,
            "model": settings.openai_model if settings.llm_enabled else None,
        }

    @app.post("/api/analyze", response_model=AnalyzeResponse)
    def analyze_endpoint(payload: AnalyzeRequest) -> AnalyzeResponse:
        return analyze(payload)

    return app


app = create_app()
