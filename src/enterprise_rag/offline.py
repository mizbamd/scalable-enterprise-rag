"""Offline knowledge preparation path."""

from __future__ import annotations

import hashlib
import math
import re
from collections import OrderedDict
from datetime import date, datetime
from typing import Iterable

from enterprise_rag.types import Chunk, Domain, SourceDoc


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _embed(text: str, dim: int = 64) -> list[float]:
    digest = hashlib.sha256(text.encode()).digest()
    raw = [((digest[i % len(digest)] / 255.0) * 2 - 1) for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in raw)) or 1.0
    return [x / norm for x in raw]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def classify_text(text: str) -> Domain:
    lower = text.lower()
    if any(w in lower for w in ("cost", "price", "supplier", "merchandis", "sku")):
        return Domain.MERCHANDISING
    if any(w in lower for w in ("shipment", "warehouse", "replenish", "logistics")):
        return Domain.SUPPLY_CHAIN
    if any(w in lower for w in ("kafka", "temporal", "aks", "finops", "platform", "rag")):
        return Domain.PLATFORM
    return Domain.GENERAL


def deduplicate(docs: Iterable[SourceDoc]) -> list[SourceDoc]:
    seen: OrderedDict[str, SourceDoc] = OrderedDict()
    for doc in docs:
        key = hashlib.sha256(normalize(doc.text).lower().encode()).hexdigest()
        if key not in seen:
            seen[key] = doc
    return list(seen.values())


def chunk_document(doc: SourceDoc, size: int = 40) -> list[Chunk]:
    words = normalize(doc.text).split()
    chunks: list[Chunk] = []
    if not words:
        return chunks
    for i in range(0, len(words), size):
        piece = " ".join(words[i : i + size])
        chunk_id = f"{doc.doc_id}:{i // size}"
        tokens = _tokenize(piece)
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                doc_id=doc.doc_id,
                text=piece,
                source_uri=doc.source_uri,
                domain=doc.domain,
                acl_roles=doc.acl_roles,
                published_at=doc.published_at,
                classification=doc.classification,
                tokens=tokens,
                vector=_embed(piece),
            )
        )
    return chunks


class HybridIndex:
    """Semantic vectors + lexical fields + ACL + freshness metadata."""

    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self._by_domain: dict[Domain, list[int]] = {d: [] for d in Domain}

    def add(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            idx = len(self.chunks)
            self.chunks.append(chunk)
            self._by_domain[chunk.domain].append(idx)

    def search(
        self,
        query: str,
        domain: Domain,
        roles: tuple[str, ...],
        as_of: date | None = None,
        top_k: int = 20,
    ) -> list[tuple[Chunk, float]]:
        as_of = as_of or date.today()
        q_tokens = _tokenize(query)
        q_vec = _embed(query)
        candidates_idx = self._by_domain.get(domain, []) + self._by_domain.get(Domain.GENERAL, [])
        # unique preserve order
        seen = set()
        ordered: list[int] = []
        for i in candidates_idx:
            if i not in seen:
                seen.add(i)
                ordered.append(i)

        scored: list[tuple[Chunk, float]] = []
        for i in ordered:
            chunk = self.chunks[i]
            if not self._acl_allows(chunk, roles):
                continue
            if not self._fresh(chunk, as_of):
                continue
            dense = sum(a * b for a, b in zip(q_vec, chunk.vector))
            overlap = len(set(q_tokens) & set(chunk.tokens))
            lexical = overlap / (1.0 + math.log(1 + len(chunk.tokens)))
            # hybrid score (vector + keyword)
            score = 0.6 * dense + 0.4 * lexical
            scored.append((chunk, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _acl_allows(chunk: Chunk, roles: tuple[str, ...]) -> bool:
        if not chunk.acl_roles:
            return True
        return bool(set(chunk.acl_roles) & set(roles)) or "platform-admin" in roles

    @staticmethod
    def _fresh(chunk: Chunk, as_of: date) -> bool:
        try:
            published = datetime.strptime(chunk.published_at, "%Y-%m-%d").date()
        except ValueError:
            return True
        age = (as_of - published).days
        return age <= chunk.freshness_days_max


class OfflinePipeline:
    """
    Offline path:
      approved sources → preserve metadata → normalize/classify/dedupe/chunk
      → embeddings → index semantic + lexical → ACL + freshness metadata
    """

    def __init__(self) -> None:
        self.index = HybridIndex()
        self.stats: dict[str, int] = {}

    def run(self, sources: list[SourceDoc]) -> HybridIndex:
        approved = [d for d in sources if d.source_uri.startswith(("https://", "sharepoint://", "lakehouse://"))]
        preserved = approved  # metadata already on SourceDoc
        normalized = [
            SourceDoc(
                doc_id=d.doc_id,
                text=normalize(d.text),
                source_uri=d.source_uri,
                domain=d.domain if d.domain != Domain.GENERAL else classify_text(d.text),
                acl_roles=d.acl_roles,
                published_at=d.published_at,
                classification=d.classification,
            )
            for d in preserved
        ]
        unique = deduplicate(normalized)
        all_chunks: list[Chunk] = []
        for doc in unique:
            all_chunks.extend(chunk_document(doc))
        self.index = HybridIndex()
        self.index.add(all_chunks)
        self.stats = {
            "ingested": len(sources),
            "approved": len(approved),
            "after_dedupe": len(unique),
            "chunks": len(all_chunks),
        }
        return self.index
