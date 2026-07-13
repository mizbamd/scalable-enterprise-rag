"""Optional FastAPI surface."""

from __future__ import annotations

from typing import Any

from enterprise_rag.system import EnterpriseRag
from enterprise_rag.types import RiskClass

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ImportError:  # pragma: no cover
    FastAPI = None  # type: ignore
    BaseModel = object  # type: ignore


rag = EnterpriseRag()
rag.prepare()


if FastAPI is not None:

    class AskBody(BaseModel):
        query: str
        principal: str = "demo-user"
        roles: list[str] = ["analyst", "merchandising"]
        use_case: str = "assistant"
        risk: str = "medium"

    app = FastAPI(title="Scalable Enterprise RAG", version="1.0.0")

    @app.get("/v1/architecture")
    def architecture() -> dict[str, Any]:
        return {
            "paths": ["offline_knowledge_preparation", "online_retrieval"],
            "monitors": [
                "retrieval_recall",
                "relevance",
                "groundedness",
                "citation_accuracy",
                "latency",
                "token_cost",
                "user_feedback",
            ],
        }

    @app.get("/v1/offline/stats")
    def offline_stats() -> dict[str, Any]:
        return rag.offline.stats

    @app.post("/v1/ask")
    def ask(body: AskBody) -> dict[str, Any]:
        risk = RiskClass(body.risk) if body.risk in {r.value for r in RiskClass} else RiskClass.MEDIUM
        resp = rag.ask(
            body.query,
            principal=body.principal,
            roles=tuple(body.roles),
            use_case=body.use_case,
            risk=risk,
        )
        return {
            "status": resp.status,
            "answer": resp.answer,
            "citations": [
                {"chunk_id": c.chunk_id, "source_uri": c.source_uri, "excerpt": c.excerpt}
                for c in resp.citations
            ],
            "domain": resp.domain.value,
            "rewritten_query": resp.rewritten_query,
            "metrics": resp.metrics,
            "correlation_id": resp.correlation_id,
        }

    @app.get("/v1/metrics")
    def metrics() -> dict[str, Any]:
        return rag.metrics.summary()

else:
    app = None  # type: ignore
