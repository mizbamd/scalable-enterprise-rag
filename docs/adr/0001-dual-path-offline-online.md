# ADR 0001: Dual-path offline / online RAG

## Status
Accepted

## Context
Collapsing indexing and serving into one request-time pipeline loses freshness control,
ACL metadata, and reproducible evaluation.

## Decision
Split into **offline knowledge preparation** and **online retrieval**. The offline path
owns ingest, metadata, dedupe, chunk, embed, hybrid index, ACL/freshness. The online path
owns auth, rewrite, domain routing, hybrid retrieve, filters, rerank, generate/abstain.

## Consequences
Indexes become versioned artifacts. Online latency excludes embedding of the full corpus.
