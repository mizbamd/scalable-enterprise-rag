"""Online retrieval path — auth → rewrite → route → hybrid → ACL → rerank → generate/abstain."""

from __future__ import annotations

import re
import time
import uuid
from typing import Any

from enterprise_rag.offline import HybridIndex, _tokenize
from enterprise_rag.risk import UseCaseProfile, classify_use_case
from enterprise_rag.types import (
    Citation,
    Domain,
    OnlineRequest,
    OnlineResponse,
    RiskClass,
)


DOMAIN_KEYWORDS: dict[Domain, tuple[str, ...]] = {
    Domain.MERCHANDISING: ("cost", "price", "supplier", "sku", "negotiation"),
    Domain.SUPPLY_CHAIN: ("shipment", "warehouse", "replenish", "logistics"),
    Domain.PLATFORM: ("kafka", "temporal", "finops", "rag", "platform", "aks"),
}


def authenticate(caller_principal: str, roles: tuple[str, ...]) -> bool:
    return bool(caller_principal) and bool(roles)


def rewrite_query(query: str) -> str:
    q = re.sub(r"\s+", " ", query).strip()
    # light expansion for enterprise jargon
    replacements = {
        "item cost": "item cost ledger effective dated cost",
        "tombstone": "cassandra tombstone compaction",
    }
    lower = q.lower()
    for src, dst in replacements.items():
        if src in lower:
            q = re.sub(re.escape(src), dst, q, flags=re.IGNORECASE)
    return q


def route_domain(query: str) -> Domain:
    lower = query.lower()
    scores = {d: sum(1 for k in keys if k in lower) for d, keys in DOMAIN_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else Domain.GENERAL


def rerank(query: str, scored: list[tuple[Any, float]], top_k: int = 5) -> list[tuple[Any, float]]:
    q = set(_tokenize(query))
    def key(item: tuple[Any, float]) -> float:
        chunk, score = item
        overlap = len(q & set(chunk.tokens))
        return overlap + score
    return sorted(scored, key=key, reverse=True)[:top_k]


def groundedness(query: str, chunks: list[Any]) -> float:
    if not chunks:
        return 0.0
    q = set(_tokenize(query))
    if not q:
        return 0.0
    covered = 0
    for token in q:
        if any(token in set(c.tokens) for c in chunks):
            covered += 1
    return covered / len(q)


def build_prompt(query: str, chunks: list[Any]) -> str:
    context = "\n".join(f"[{c.chunk_id}] ({c.source_uri}) {c.text}" for c in chunks)
    return (
        "Answer using ONLY the context. Cite chunk ids. "
        "If evidence is insufficient, abstain.\n\n"
        f"Context:\n{context}\n\nQuestion: {query}"
    )


def generate_or_abstain(
    query: str,
    chunks: list[Any],
    profile: UseCaseProfile,
) -> tuple[str, str, list[Citation], float]:
    g = groundedness(query, chunks)
    if not chunks or g < profile.min_groundedness:
        return (
            "abstain",
            "Insufficient grounded evidence in permitted indexes — abstaining.",
            [],
            g,
        )
    # extractive answer with citations
    excerpts = [c.text for c in chunks[:3]]
    answer = " ".join(excerpts)
    citations = [
        Citation(chunk_id=c.chunk_id, source_uri=c.source_uri, excerpt=c.text[:180])
        for c in chunks[:3]
    ]
    if profile.risk == RiskClass.HIGH and g < 0.8 and len(citations) < 2:
        return (
            "abstain",
            "High-risk use case requires stronger multi-source evidence — abstaining.",
            citations,
            g,
        )
    return "answer", answer, citations, g


class OnlinePipeline:
    """
    Online path:
      authenticate → classify/rewrite query → route domain index
      → hybrid retrieval → ACL/metadata filters → rerank
      → bounded prompt + citations → generate / validate / answer or abstain
    """

    def __init__(self, index: HybridIndex) -> None:
        self.index = index
        self.feedback: list[dict[str, Any]] = []

    def run(self, request: OnlineRequest) -> OnlineResponse:
        t0 = time.perf_counter()
        cid = request.correlation_id or str(uuid.uuid4())
        profile = classify_use_case(request.use_case)

        if not authenticate(request.caller.principal, request.caller.roles):
            return OnlineResponse(
                status="abstain",
                answer="Authentication failed.",
                citations=[],
                domain=Domain.GENERAL,
                rewritten_query=request.query,
                metrics={"error": "auth"},
                correlation_id=cid,
            )

        # risk from request overrides profile when stricter
        if request.risk.value == "high":
            profile = classify_use_case("regulated")

        rewritten = rewrite_query(request.query)
        domain = route_domain(rewritten)
        hybrid = self.index.search(
            rewritten,
            domain=domain,
            roles=request.caller.roles,
            top_k=20,
        )
        ranked = rerank(rewritten, hybrid, top_k=5)
        chunks = [c for c, _ in ranked]
        prompt = build_prompt(rewritten, chunks)
        status, answer, citations, g = generate_or_abstain(rewritten, chunks, profile)
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        token_cost = round(0.000002 * max(1, len(prompt.split()) + len(answer.split())), 6)

        metrics = {
            "retrieval_candidates": len(hybrid),
            "reranked": len(ranked),
            "groundedness": round(g, 3),
            "citation_count": len(citations),
            "latency_ms": latency_ms,
            "token_cost_usd": token_cost,
            "domain": domain.value,
            "risk": profile.risk.value,
            "prompt_chars": len(prompt),
        }
        return OnlineResponse(
            status=status,
            answer=answer,
            citations=citations,
            domain=domain,
            rewritten_query=rewritten,
            metrics=metrics,
            correlation_id=cid,
        )

    def record_feedback(self, correlation_id: str, relevant: bool, note: str = "") -> None:
        self.feedback.append(
            {"correlation_id": correlation_id, "relevant": relevant, "note": note}
        )
