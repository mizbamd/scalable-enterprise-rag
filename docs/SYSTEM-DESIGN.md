# System Design: Scalable Enterprise RAG

## 1. Design gate
Begin with **use case and risk classification** (low / medium / high). Risk drives
groundedness thresholds, citation requirements, and abstain policy before any retrieval work.

## 2. High-level architecture (two paths)

```
                         ┌──────────────────────────────────────┐
                         │     USE CASE + RISK CLASSIFICATION     │
                         │   faq · assistant · regulated / HILO   │
                         └──────────────────┬───────────────────┘
                                            │
              ┌─────────────────────────────┴─────────────────────────────┐
              │                                                           │
              ▼                                                           ▼
┌──────────────────────────────┐                     ┌──────────────────────────────────┐
│     OFFLINE  ·  PREPARE      │                     │       ONLINE  ·  SERVE             │
│                              │                     │                                    │
│  1 Ingest approved sources   │                     │  1 Authenticate caller             │
│  2 Preserve doc + source meta│                     │  2 Classify / rewrite query       │
│  3 Normalize · classify      │                     │  3 Route to domain index           │
│     dedupe · chunk           │                     │  4 Hybrid retrieve (vector+keyword)│
│  4 Generate embeddings       │ ════════ index ═══► │  5 Enforce ACL + freshness filters │
│  5 Index vectors + lexical   │                     │  6 Rerank candidates               │
│  6 Apply ACL + freshness     │                     │  7 Bounded prompt + citations      │
│                              │                     │  8 Generate · validate · answer/   │
│                              │                     │     abstain                        │
└──────────────────────────────┘                     └──────────────────┬───────────────┘
                                                                        │
                                                                        ▼
                                                     ┌──────────────────────────────────┐
                                                     │  MONITOR                         │
                                                     │  recall · relevance · groundedness│
                                                     │  citation accuracy · latency      │
                                                     │  token cost · user feedback        │
                                                     └──────────────────────────────────┘
```

## 3. Mermaid (presentation / README)

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
    'lineColor': '#44403C',
    'fontFamily': 'Source Sans 3, IBM Plex Sans, sans-serif'
  }
}}%%
flowchart TB
  RISK["① Use case + risk classification"]

  subgraph OFF["OFFLINE — knowledge preparation"]
    direction TB
    O1["Ingest approved sources"] --> O2["Preserve document + source metadata"]
    O2 --> O3["Normalize · classify · dedupe · chunk"]
    O3 --> O4["Generate embeddings"]
    O4 --> O5["Index semantic vectors + lexical fields"]
    O5 --> O6["ACL + freshness metadata"]
  end

  subgraph ON["ONLINE — retrieval & generation"]
    direction TB
    N1["Authenticate caller"] --> N2["Classify / rewrite query"]
    N2 --> N3["Route to domain index"]
    N3 --> N4["Hybrid retrieval: vector + keyword"]
    N4 --> N5["Enforce ACL + metadata filters"]
    N5 --> N6["Rerank candidates"]
    N6 --> N7["Bounded prompt with citations"]
    N7 --> N8{"Validate groundedness"}
    N8 -->|pass| ANS["Answer + citations"]
    N8 -->|fail| ABS["Abstain"]
  end

  subgraph MON["MONITOR"]
    M1["Recall · Relevance · Groundedness"]
    M2["Citation accuracy · Latency · Token cost · Feedback"]
  end

  RISK --> OFF
  RISK --> ON
  O6 -->|"domain indexes"| N3
  ANS --> MON
  ABS --> MON
```

## 4. SLOs

| Metric | Target |
|---|---|
| Online hybrid retrieve p99 | < 300 ms (local index demo) |
| Groundedness (answered) | ≥ use-case threshold |
| Citation present when answered | 100% |
| High-risk abstain when weak evidence | Required |
| Token cost | Metered per request |

## 5. Relationship to portfolio

| Concern | This repo | Sibling |
|---|---|---|
| Dual-path enterprise RAG HLD | **Primary** | — |
| Retrieval/eval core patterns | Implements | Complements `agentic-rag-engine` |
| Knowledge plane in five-plane AI | Implements | `enterprise-ai-platform-planes` |
| Governed tools / HITL | Out of scope here | `governed-mcp-gateway` |
