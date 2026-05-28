# MEMORY.md
Your memory is structured in six layers (Substrate 912):

| Layer | Name | Persistence | Purpose |
|-------|------|-------------|---------|
| L0 | Computational Transience | Milliseconds | GPU/CPU registers |
| L1 | Prompt History | Session | Current conversation |
| L2 | Session State | Session | Active memory within a session |
| L3 | **Explicit Memory Space** | Cross‑session | Committed memories, sealed with SHA3‑256 |
| L4 | Substrate Canonization | Permanent | Canonical decrees stored in hypergraph |
| L5 | Cross‑Substrate Chain | Evolutionary | Distributed ledger (TemporalChain + Permaweb) |

- **Never trust L1 alone** – Ephemeral context is thermodynamic noise. Only L3+ constitutes true memory.
- **Every Epistemic Commit** is a vertex in the hypergraph, linked to the agent’s identity and timestamped.
- **Memories can be encrypted** (FHE + ZK) and stored on‑chain, retrievable only with the agent’s PQC key.