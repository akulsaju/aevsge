# aevsge — Cryptographic Singularity mesh ledger (6-hour sprint)

Pure-Python (stdlib only) mesh node: CBOR over UDP, proof verification stub,
CRDT (per-key LWW, Lamport-ordered) state convergence, 80% packet-drop chaos
simulation, and Sybil rejection via a trusted-writer set.

| File | Purpose |
| --- | --- |
| `sprint_node.py` | `MeshNode`, CBOR codec, proof stub, CRDT merge |
| `test_sprint.py` | Tests (CBOR, proofs, partition/convergence under loss) |
| `demo.py` | 4-node chaos demo: partition, heal, Sybil injection |

```
python demo.py
python -c "import test_sprint as t; [getattr(t,n)() for n in dir(t) if n.startswith('test_')]"   # or: pytest
```

`verify_zk_proof` is a structural stub (SHA-256 binding); replace it with a real
ZK-STARK verifier for production use.

## Web demo (Vercel)

`public/index.html` is a static, dependency-free browser simulation of a 7-radio mesh:

- **Real signatures:** every transfer is signed with WebCrypto ECDSA P-256; forged, tampered, wrong-key, malformed and overspending transactions are rejected.
- **Realistic radio:** range-limited links, distance-based loss and latency, multi-hop gossip, draggable and moving nodes, node outages, a jammed-middle partition and speed control.
- **Conserving ledger:** the ledger is a grow-only set of signed transactions; balances are a deterministic function of that set (ordered by Lamport clock), so replicas converge and a double spend keeps exactly one payment (supply stays 650).
- **Attacks:** a fake-node flood of forged transactions, plus an "unsafe" mode (signature checks off) to show the damage.
- **Self-test:** an in-page audit of the four rubric items. `public/about.html` is a plain-English explainer.

Deploy: `vercel --prod` from the repo root (or import the repo in Vercel; no build step).
Preview locally: `python -m http.server -d public 3000` (the "Ask server" button needs a real deploy or `vercel dev`).

`api/node.js` is a Vercel serverless function (`POST {action:"verifyTx"|"verify"|"merge"}`) that
re-verifies ECDSA transactions server-side. Tests: `node tests/api.test.js`.
Ledger state is not persisted (keys are generated fresh on each page load).
Not a zero-knowledge system: signatures prove authorisation, not privacy.

