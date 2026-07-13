"""Use case + risk classification — first design gate before any RAG path."""

from __future__ import annotations

from dataclasses import dataclass

from enterprise_rag.types import RiskClass


@dataclass(frozen=True)
class UseCaseProfile:
    name: str
    risk: RiskClass
    require_citations: bool
    min_groundedness: float
    allow_abstain: bool
    description: str


PROFILES: dict[str, UseCaseProfile] = {
    "faq": UseCaseProfile(
        "faq",
        RiskClass.LOW,
        require_citations=True,
        min_groundedness=0.35,
        allow_abstain=True,
        description="Public or low-stakes FAQ",
    ),
    "assistant": UseCaseProfile(
        "assistant",
        RiskClass.MEDIUM,
        require_citations=True,
        min_groundedness=0.45,
        allow_abstain=True,
        description="Internal operator assistant",
    ),
    "regulated": UseCaseProfile(
        "regulated",
        RiskClass.HIGH,
        require_citations=True,
        min_groundedness=0.65,
        allow_abstain=True,
        description="Regulated / commercial advice — abstain by default if weak evidence",
    ),
}


def classify_use_case(name: str) -> UseCaseProfile:
    if name not in PROFILES:
        return PROFILES["assistant"]
    return PROFILES[name]
