# scalable-enterprise-rag

[![CI](https://github.com/mizbamd/scalable-enterprise-rag/actions/workflows/ci.yml/badge.svg)](./.github/workflows/ci.yml)

> **Scalable enterprise RAG architecture** — start with use-case and risk classification, then
> run two paths: **offline knowledge preparation** and **online retrieval**. Hybrid vector +
> keyword search, ACL and freshness filters, reranking, bounded prompts with citations, and
> **answer or abstain**. Ops monitors recall, relevance, groundedness, citation accuracy,
> latency, token cost, and user feedback.

Complements [`agentic-rag-engine`](https://github.com/mizbamd/agentic-rag-engine) (retrieval core)
and [`enterprise-ai-platform-planes`](https://github.com/mizbamd/enterprise-ai-platform-planes)
(knowledge plane contract). **This repo owns the end-to-end dual-path enterprise design.**

## High-level architecture

```
                         ┌──────────────────────────────────────┐
                         │     USE CASE + RISK CLASSIFICATION     │
                         └──────────────────┬───────────────────┘
              ┌─────────────────────────────┴─────────────────────────────┐
              ▼                                                           ▼
┌──────────────────────────────┐                     ┌──────────────────────────────────┐
│     OFFLINE  ·  PREPARE      │                     │       ONLINE  ·  SERVE             │
│  Ingest approved sources     │                     │  Authenticate caller               │
│  Preserve metadata           │                     │  Classify / rewrite query         │
│  Normalize·classify·dedupe   │                     │  Route to domain index             │
│  Chunk → embeddings          │ ════ domain ══════► │  Hybrid: vector + keyword          │
│  Index vectors + lexical     │      indexes        │  ACL + freshness filters           │
│  ACL + freshness metadata    │                     │  Rerank → cited prompt             │
│                              │                     │  Generate · validate · answer/abstain│
└──────────────────────────────┘                     └──────────────────┬───────────────┘
                                                                        ▼
                                                     ┌──────────────────────────────────┐
                                                     │ MONITOR: recall · relevance ·      │
                                                     │ groundedness · citations · latency │
                                                     │ token cost · user feedback         │
                                                     └──────────────────────────────────┘
```

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#FEF3C7',
    'primaryBorderColor': '#D97706',
    'secondaryColor': '#DBEAFE',
    'secondaryBorderColor': '#1D4ED8',
    'tertiaryColor': '#D1FAE5',
    'tertiaryBorderColor': '#047857',
    'lineColor': '#44403C'
  }
}}%%
flowchart TB
  RISK["① Use case + risk classification"]
  subgraph OFF["OFFLINE — knowledge preparation"]
    O1["Ingest approved sources"] --> O2["Preserve metadata"]
    O2 --> O3["Normalize · classify · dedupe · chunk"]
    O3 --> O4["Embeddings"] --> O5["Vector + lexical index"]
    O5 --> O6["ACL + freshness"]
  end
  subgraph ON["ONLINE — retrieval"]
    N1["Authenticate"] --> N2["Rewrite query"] --> N3["Route domain"]
    N3 --> N4["Hybrid retrieve"] --> N5["ACL + freshness"]
    N5 --> N6["Rerank"] --> N7["Bounded prompt + citations"]
    N7 --> N8{"Validate"}
    N8 -->|pass| ANS["Answer"]
    N8 -->|fail| ABS["Abstain"]
  end
  RISK --> OFF & ON
  O6 --> N3
  ANS & ABS --> MON["Monitor: recall · groundedness · latency · cost · feedback"]
```

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install pytest
pytest -q
./scripts/demo.sh
```

### API (optional)
```bash
pip install fastapi uvicorn pydantic
PYTHONPATH=src uvicorn enterprise_rag.api:app --port 8091
# POST /v1/ask  {"query": "..."}
# GET  /v1/metrics
# GET  /v1/architecture
```

## Documentation
- [`docs/SYSTEM-DESIGN.md`](docs/SYSTEM-DESIGN.md) — full HLD + SLOs
- ADRs: [`docs/adr/`](docs/adr/)

## Toolbox
`Python` · `Hybrid RAG` · `ACL` · `Freshness` · `Domain routing` · `Abstain/guardrails` · `Ops metrics` · `FastAPI`
