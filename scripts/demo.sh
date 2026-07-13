#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH=src

python - <<'PY'
from enterprise_rag.system import EnterpriseRag
from enterprise_rag.types import RiskClass

rag = EnterpriseRag()
print("=== Offline prepare ===")
print(rag.prepare())

print("\n=== Online ask (merchandising) ===")
r = rag.ask("How does item cost ledger work with Kafka?")
print(f"status={r.status} domain={r.domain.value}")
print(f"answer={r.answer[:160]}...")
print(f"citations={len(r.citations)} metrics={r.metrics}")

print("\n=== High-risk abstain path ===")
r2 = rag.ask("unknown xyzzy topic with no evidence", use_case="regulated", risk=RiskClass.HIGH)
print(f"status={r2.status} answer={r2.answer}")

print("\n=== Ops summary ===")
print(rag.metrics.summary())
print("OK")
PY
