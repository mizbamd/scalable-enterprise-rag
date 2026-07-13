"""Enterprise RAG system — wires offline prep + online serving."""

from __future__ import annotations

from enterprise_rag.metrics import MetricsCollector
from enterprise_rag.offline import OfflinePipeline
from enterprise_rag.online import OnlinePipeline
from enterprise_rag.types import Caller, Domain, OnlineRequest, RiskClass, SourceDoc


SAMPLE_SOURCES = [
    SourceDoc(
        doc_id="doc-cost-1",
        text=(
            "Item cost ledger uses CQRS and Temporal for effective-dated cost changes. "
            "Negotiation execution publishes cost.facts to Kafka for projection."
        ),
        source_uri="lakehouse://merchandising/cost-ledger.md",
        domain=Domain.MERCHANDISING,
        acl_roles=("analyst", "merchandising"),
        published_at="2026-01-15",
        classification="internal",
    ),
    SourceDoc(
        doc_id="doc-supplier-1",
        text=(
            "Supplier golden record merges multi-source MDM via Kafka CDC. "
            "Canonical supplier identity resolves aliases for price and cost systems."
        ),
        source_uri="https://wiki.example/supplier-golden-record",
        domain=Domain.MERCHANDISING,
        acl_roles=("analyst", "merchandising"),
        published_at="2026-02-01",
        classification="internal",
    ),
    SourceDoc(
        doc_id="doc-platform-1",
        text=(
            "Enterprise RAG uses hybrid retrieval with vector plus keyword indexes. "
            "FinOps monitors latency and token cost for every online request."
        ),
        source_uri="https://wiki.example/enterprise-rag",
        domain=Domain.PLATFORM,
        acl_roles=("analyst", "platform"),
        published_at="2026-03-10",
        classification="internal",
    ),
    SourceDoc(
        doc_id="doc-regulated-1",
        text=(
            "Commercial rebate terms and unit cost negotiations are regulated retail data. "
            "Answers must cite sources and abstain when evidence is weak."
        ),
        source_uri="sharepoint://compliance/retail-redaction.md",
        domain=Domain.MERCHANDISING,
        acl_roles=("compliance", "merchandising"),
        published_at="2026-04-01",
        classification="regulated",
    ),
    SourceDoc(
        doc_id="doc-dupe",
        text=(
            "Item cost ledger uses CQRS and Temporal for effective-dated cost changes. "
            "Negotiation execution publishes cost.facts to Kafka for projection."
        ),
        source_uri="lakehouse://merchandising/cost-ledger-copy.md",
        domain=Domain.MERCHANDISING,
        acl_roles=("analyst", "merchandising"),
        published_at="2026-01-15",
        classification="internal",
    ),
]


class EnterpriseRag:
    def __init__(self) -> None:
        self.offline = OfflinePipeline()
        self.online: OnlinePipeline | None = None
        self.metrics = MetricsCollector()

    def prepare(self, sources: list[SourceDoc] | None = None) -> dict:
        index = self.offline.run(sources or SAMPLE_SOURCES)
        self.online = OnlinePipeline(index)
        return dict(self.offline.stats)

    def ask(
        self,
        query: str,
        principal: str = "demo-user",
        roles: tuple[str, ...] = ("analyst", "merchandising"),
        use_case: str = "assistant",
        risk: RiskClass = RiskClass.MEDIUM,
    ):
        if self.online is None:
            self.prepare()
        assert self.online is not None
        response = self.online.run(
            OnlineRequest(
                query=query,
                caller=Caller(principal=principal, roles=roles),
                use_case=use_case,
                risk=risk,
            )
        )
        self.metrics.observe(response)
        return response
