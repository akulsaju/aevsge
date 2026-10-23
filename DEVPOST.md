## 🛡️ NodeArmor: a shared bank book that survives 80% packet loss

NodeArmor is our entry for the Cryptographic Singularity 6-hour sprint. It is a mesh ledger where nodes pass **signed transfers** to whoever is in radio range, lose most packets on the way, and still end up with **identical books**.

Think of a village after a storm. No internet, no bank. Everyone keeps a notebook and shouts notes to neighbours, and most shouts get lost. NodeArmor makes sure all the notebooks end up the same and nobody can cheat.

## 🎮 Try it out

- Live demo: [aevsge.vercel.app](https://aevsge.vercel.app/)
- Code: [github.com/akulsaju/aevsge](https://github.com/akulsaju/aevsge)

Buttons to press in the demo:

- **Send**: a signed payment hops across the mesh.
- **Cheat: forge signature**: every node rejects the forged payment.
- **Cheat: overspend**: signed, but more than the sender owns, so it is refused.
- **Jam the middle**: the network splits, the books diverge, then heal.
- **Attack: fake-node flood**: a fake node spams forgeries and gets blocked.
- **Run automated audit**: grades all four rubric items live.

## ✅ Rubric coverage

| Deliverable | Weight | Status |
| --- | --- | --- |
| Mesh socket connectivity (CBOR over UDP, multi-hop gossip) | 30% | Done |
| Proof / signature verification, rejects invalid input | 30% | Done |
| CRDT convergence after a partition | 25% | Done |
| Chaos survival at 80% packet drop | 15% | Done |

## 🧠 How it works

1. Alice signs a payment with a real ECDSA P-256 key (WebCrypto).
2. The payment is gossiped over a lossy, range-limited radio mesh.
3. Every node checks the signature. Forged, tampered, wrong-key, malformed and overspending transactions are rejected.
4. Valid transactions go into a grow-only set, ordered by Lamport clock then id.
5. Every node computes the same balances from the same set, so replicas converge and a double spend keeps exactly one payment. Total supply stays 650.

## 📡 Realism

- Range-limited links, distance-based loss and latency
- Draggable and moving nodes, node outages, jammed-middle partitions
- Fake-node flood attack, plus an unsafe mode (signature checks off) to show the damage

## 🐍 Python reference node

Pure Python, stdlib only: CBOR over UDP, proof stub, per-key LWW CRDT, 80% drop simulation and a trusted-writer Sybil filter.

- sprint_node.py: MeshNode, CBOR codec, proof stub, CRDT merge
- test_sprint.py: tests for CBOR, proofs, partition and convergence under loss
- demo.py: 4-node chaos demo (partition, heal, Sybil injection)

Run it:

```
python demo.py
node tests/api.test.js
```

Deploy it:

```
vercel --prod
```

The file api/node.js is a Vercel serverless function that re-verifies ECDSA transactions on the server.

## ⚠️ Honest limits

- Signatures prove who authorised a payment. This is not a zero-knowledge system.
- A double spend is resolved by a fixed tie-break rule, not true global ordering.
- The Python verify_zk_proof is a structural stub. A real ZK-STARK verifier would replace it in production.
- Ledger state is not persisted. Keys are generated fresh on each page load.

Built in a 6-hour sprint 🔥 Mesh. Prove. Converge. Survive.
