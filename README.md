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

`public/index.html` is a static, dependency-free browser simulation of the mesh
(drop-rate slider, partition toggle, transfers, forged proofs, Sybil injection).
Deploy: `vercel --prod` from the repo root (or import the repo in Vercel; no build step).
Preview locally: `python -m http.server -d public 3000`.