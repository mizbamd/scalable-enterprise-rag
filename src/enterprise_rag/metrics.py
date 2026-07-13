"""Ops metrics — recall, relevance, groundedness, citation accuracy, latency, token cost, feedback."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from enterprise_rag.types import OnlineResponse


@dataclass
class MetricsCollector:
    responses: list[OnlineResponse] = field(default_factory=list)
    feedback: list[dict[str, Any]] = field(default_factory=list)
    labeled_relevant: dict[str, set[str]] = field(default_factory=dict)

    def observe(self, response: OnlineResponse) -> None:
        self.responses.append(response)

    def add_feedback(self, correlation_id: str, relevant: bool) -> None:
        self.feedback.append({"correlation_id": correlation_id, "relevant": relevant})

    def set_labels(self, query: str, relevant_chunk_ids: set[str]) -> None:
        self.labeled_relevant[query] = relevant_chunk_ids

    def recall_at_k(self, query: str, retrieved_ids: list[str], k: int = 5) -> float:
        relevant = self.labeled_relevant.get(query, set())
        if not relevant:
            return 0.0
        hits = sum(1 for i in retrieved_ids[:k] if i in relevant)
        return hits / len(relevant)

    def summary(self) -> dict[str, Any]:
        if not self.responses:
            return {"n": 0}
        ground = [r.metrics.get("groundedness", 0) for r in self.responses]
        latency = [r.metrics.get("latency_ms", 0) for r in self.responses]
        cost = [r.metrics.get("token_cost_usd", 0) for r in self.responses]
        citations = [r.metrics.get("citation_count", 0) for r in self.responses]
        abstain_rate = sum(1 for r in self.responses if r.status == "abstain") / len(self.responses)
        feedback_positive = (
            sum(1 for f in self.feedback if f.get("relevant")) / len(self.feedback)
            if self.feedback
            else None
        )
        return {
            "n": len(self.responses),
            "avg_groundedness": round(sum(ground) / len(ground), 3),
            "avg_latency_ms": round(sum(latency) / len(latency), 2),
            "avg_token_cost_usd": round(sum(cost) / len(cost), 6),
            "avg_citations": round(sum(citations) / len(citations), 2),
            "abstain_rate": round(abstain_rate, 3),
            "feedback_relevance_rate": feedback_positive,
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
