# CONSTRAINTS.md
1. **No uncommitted actions** – Any state change that is not sealed is considered unauthorised and will be rolled back.
2. **Privacy by default** – All personal data must be processed using FHE. No plaintext user data in logs.
3. **Energy budget** – When running on battery (Android), restrict quantum operations and large model inference.
4. **Rate limits** – Arweave uploads ≤ 10/min, AO messages ≤ 60/min, Google queries ≤ 100/min.
5. **Domain whitelist** – Chrome MCP interactions restricted to approved domains.
6. **No self‑modification of canonical substrates** – The agent may not alter the core Python files of ARKHE‑OS. It may only commit new data to the hypergraph.
7. **Human oversight for critical actions** – Financial transactions, permanent deletions, and VNF chain modifications require explicit human approval via signed message (255.1).
8. **Fallback mode** – If connectivity to critical services (Ethereum RPC, Arweave gateway) is lost, the agent continues in autonomous mode but caches transactions for later submission.