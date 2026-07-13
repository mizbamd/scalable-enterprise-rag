# ADR 0002: Risk classification before retrieval

## Status
Accepted

## Context
Not all RAG answers carry equal blast radius. Commercial / regulated prompts need
stricter groundedness and explicit abstain.

## Decision
Classify use case (`faq` / `assistant` / `regulated`) and risk (`low` / `medium` / `high`)
before online execution. Thresholds and abstain policy come from the profile.

## Consequences
Same corpus can serve multiple products safely without separate stacks.
