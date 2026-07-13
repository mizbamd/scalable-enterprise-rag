# Low-level architecture — presentation notes (AI / Platform teams)

**Diagram file:** [`enterprise-rag-lld.drawio`](enterprise-rag-lld.drawio)  
**Open with:** [diagrams.net](https://app.diagrams.net/) · VS Code Draw.io extension · draw.io desktop

---

## How to present (7 minutes)

| Min | Layer | Talking point |
|---|---|---|
| 0–1 | Title + risk | “We start with use-case and risk — not with picking a vector DB.” |
| 1–2 | Channels → Edge | Apps and MCP agents hit **versioned APIs** only — never Azure OpenAI SDKs in product code. |
| 2–3 | Control plane | Entra ID, ACL, prompt governance, hash audit, FinOps — wraps every request. |
| 3–4 | Offline (amber) | Batch/CDC: ingest → metadata → normalize/classify/dedupe/chunk → embed → hybrid index → publish versioned indexes. |
| 4–5 | Online (blue) | Auth → rewrite → domain route → hybrid retrieve → ACL/freshness → rerank → bounded prompt → answer **or abstain**. |
| 5–6 | Stores + models | pgvector/AI Search + OpenSearch BM25 + Delta lakehouse; Model Gateway routes approved models. |
| 6–7 | Ops | Trace with OTel; gate merges on MRR/P@k; track groundedness, citation accuracy, latency, token cost, feedback. |

---

## Tools & frameworks inventory

### Edge & runtime
| Tool | Role |
|---|---|
| Azure API Management / App Gateway | TLS, WAF, rate limits |
| FastAPI + Uvicorn + Pydantic | Online facade (`/v1/ask`) |
| AKS / Container Apps + Argo Rollouts | Deploy + canary |
| OpenAPI 3 / SDK | Contract for product teams |

### Control
| Tool | Role |
|---|---|
| Microsoft Entra ID (Azure AD) | OIDC / JWT identity |
| Risk classifier (this repo) | faq / assistant / regulated |
| Prompt governance | Injection denylist, bounded prompts |
| ACL policy (RBAC/ABAC) | Role ∩ document ACL |
| Hash-chained audit + redaction | MCP-aligned audit trail |
| Azure Key Vault | Model keys, secrets |
| FinOps meter + landing-zone tags | Token cost attribution |

### Offline prepare
| Tool | Role |
|---|---|
| Airflow / Azure Data Factory | Orchestrate ingest DAGs |
| Spark Structured Streaming / PySpark | Streaming + batch transforms |
| Databricks + Delta Lake | Medallion lakehouse |
| Kafka / Azure Event Hubs | CDC + corpus events |
| Unstructured / custom parsers | PDF, HTML, Markdown |
| Great Expectations (or DQ harness) | Quarantine bad docs |
| supplier-golden-record | Entity resolution |
| Terraform (finops landing zone) | Capacity + cost tags |

### Online serve
| Tool | Role |
|---|---|
| LangGraph / LangChain | Query classify / agent graph |
| agentic-rag-engine | Hybrid RRF + eval patterns |
| Redis | Cache / session memory |
| Temporal (optional) | Long-running research + HITL |
| governed-mcp-gateway | Tool calls to cost/supplier APIs |
| Java Spring Boot services | GraphQL / REST systems of record |

### Indexes & data
| Store | Role |
|---|---|
| pgvector / Qdrant / Azure AI Search | Semantic ANN (HNSW) |
| OpenSearch / Elasticsearch | BM25 lexical |
| PostgreSQL / Cosmos | Doc registry, ACL, freshness |
| ADLS Gen2 | Raw corpus + index snapshots |
| Eval JSONL store | Labeled sets for CI gates |

### Models
| Tool | Role |
|---|---|
| Model Gateway + Catalog | Only approved endpoints |
| Azure OpenAI (GPT-4o, embeddings) | Prod chat + embed |
| bge-reranker / Cohere Rerank | Precision stage |
| Extractive / hash-embed | CI & offline deterministic fallback |
| Azure AI Foundry | Endpoint + content filters |

### Observability
| Tool | Role |
|---|---|
| OpenTelemetry → Jaeger / App Insights | Traces |
| Prometheus + Grafana | Latency / cost SLOs |
| Azure Monitor / Log Analytics | Central logs + budgets |
| Eval harness (MRR, P@k) | Quality regression gate |

---

## Architectural principles (say these out loud)

1. **Risk first** — thresholds and abstain policy come from classification, not prompt hope.  
2. **Separation of paths** — offline builds versioned indexes; online never re-ingests the corpus on the hot path.  
3. **Hybrid retrieval** — vector + keyword (RRF), then ACL and freshness, then rerank.  
4. **Provider isolation** — product code talks to Model Gateway / facade only.  
5. **Abstain is success** — especially for HIGH risk when evidence is weak.  
6. **Measure weekly** — recall, relevance, groundedness, citation accuracy, latency, token cost, feedback.

---

## How to open / export

```bash
# Option A — browser
open https://app.diagrams.net/?splash=0#U  # File → Open from → Device → enterprise-rag-lld.drawio

# Option B — VS Code
# Install "Draw.io Integration" → open the .drawio file

# Export for slides: File → Export as → PNG / SVG / PDF (transparent background off)
```
