"""Shared types for scalable enterprise RAG."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskClass(str, Enum):
    LOW = "low"          # FAQ, public policy — answer freely when grounded
    MEDIUM = "medium"    # internal runbooks — ACL + citations required
    HIGH = "high"        # regulated / commercial — abstain unless strong evidence


class Domain(str, Enum):
    MERCHANDISING = "merchandising"
    SUPPLY_CHAIN = "supply_chain"
    PLATFORM = "platform"
    GENERAL = "general"


@dataclass(frozen=True)
class SourceDoc:
    doc_id: str
    text: str
    source_uri: str
    domain: Domain
    acl_roles: tuple[str, ...]
    published_at: str  # ISO date
    classification: str  # public | internal | regulated


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    source_uri: str
    domain: Domain
    acl_roles: tuple[str, ...]
    published_at: str
    classification: str
    freshness_days_max: int = 365
    tokens: list[str] = field(default_factory=list)
    vector: list[float] = field(default_factory=list)


@dataclass
class Caller:
    principal: str
    roles: tuple[str, ...]


@dataclass
class OnlineRequest:
    query: str
    caller: Caller
    use_case: str = "assistant"
    risk: RiskClass = RiskClass.MEDIUM
    correlation_id: str = ""


@dataclass
class Citation:
    chunk_id: str
    source_uri: str
    excerpt: str


@dataclass
class OnlineResponse:
    status: str  # answer | abstain
    answer: str
    citations: list[Citation]
    domain: Domain
    rewritten_query: str
    metrics: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""
