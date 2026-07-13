# ADR 0003: Hybrid retrieval with ACL and freshness

## Status
Accepted

## Context
Vector-only search misses identifiers; keyword-only misses paraphrase. Enterprise corpora
also require authorization and stale-document exclusion.

## Decision
Index **semantic vectors and lexical fields**. At query time: domain route → hybrid score →
**ACL role intersection** → **freshness window** → rerank → bounded cited prompt.

## Consequences
Slightly higher filter cost; prevents unauthorized and stale grounded answers.
