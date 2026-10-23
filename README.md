<div align="center">

![NodeArmor animated banner](https://raw.githubusercontent.com/akulsaju/aevsge/main/assets/banner.svg)

[![Typing SVG](https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=22&duration=2800&pause=900&color=00E5FF&center=true&vCenter=true&width=760&lines=Signed+money+notes+over+a+lossy+radio+mesh;Forged+transactions+get+rejected;Replicas+converge+after+a+network+partition;80%25+packet+loss%3A+still+no+crash)](https://github.com/akulsaju/aevsge)

![Python](https://img.shields.io/badge/Python-stdlib_only-3776AB?style=for-the-badge&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/WebCrypto-ECDSA_P--256-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Vercel](https://img.shields.io/badge/Vercel-ready-000000?style=for-the-badge&logo=vercel&logoColor=white)
![CRDT](https://img.shields.io/badge/CRDT-converges-2BFF9A?style=for-the-badge)
![Chaos](https://img.shields.io/badge/Chaos_test-80%25_loss-FF3B5C?style=for-the-badge)
![Tests](https://img.shields.io/badge/audit-4%2F4_passing-00E5FF?style=for-the-badge)

### 🛡️ A shared bank book that keeps working when the network is bad, down or under attack.

</div>

---

## 🌈 What is it?

**NodeArmor** is our entry for the *Cryptographic Singularity* 6-hour sprint: a mesh ledger where nodes pass **signed transfers** to whoever is in radio range, lose most packets on the way, and **still end up with identical books**.

> Think of a village after a storm. No internet, no bank. Everyone keeps a notebook, shouts notes to neighbours, and most shouts get lost. NodeArmor makes sure all notebooks end up the same and nobody can cheat.

## 🎮 Live demo

Open `public/index.html` (or the Vercel deploy) and try:

| Button | What it shows |
| --- | --- |
| 💸 **Send** | A signed payment hopping across the mesh |
| 🕵️ **Cheat: forge signature** | A forged payment is rejected by every node |
| 💰 **Cheat: overspend** | Signed but more than the sender owns, refused |
| 🧱 **Jam the middle** | A network partition; books diverge, then heal |
| 📡 **Attack: fake-node flood** | A Sybil node spams forgeries and gets blocked |
| 🧪 **Run automated audit** | Grades all four rubric items live |

## ✅ Scoring rubric coverage

| Deliverable | Weight | Status |
| --- | --- | --- |
| 📶 Mesh socket connectivity (CBOR over UDP, multi-hop gossip) | 30% | ✅ |
| 🔐 Proof / signature verification, rejects invalid input | 30% | ✅ |
| 🔁 CRDT convergence after partition | 25% | ✅ |
| 🌪️ Chaos survival at 80% packet drop | 15% | ✅ |

## 🧠 How it works

```mermaid
flowchart LR
    A[Alice signs a payment] --> B[Gossip over lossy radio]
    B --> C{Signature valid?}
    C -- no --> X[Rejected]
    C -- yes --> D[Add to grow-only tx set]
    D --> E[Sort by Lamport clock then id]
    E --> F[Same balances on every node]
```

- **Real signatures:** every transfer is signed with WebCrypto **ECDSA P-256**. Forged, tampered, wrong-key, malformed and overspending transactions are rejected.
- **Realistic radio:** range-limited links, distance-based loss and latency, draggable and moving nodes, outages, jammed-middle partitions.
- **Conserving ledger:** a grow-only set of signed transactions with deterministic ordering, so replicas converge and a double spend keeps exactly one payment (supply stays 650).
- **Attacks:** fake-node flood, plus an unsafe mode (signature checks off) to show the damage.

## 🐍 Python reference node

Pure Python, stdlib only: CBOR over UDP, proof stub, per-key LWW CRDT, 80% drop simulation and a trusted-writer Sybil filter.

| File | Purpose |
| --- | --- |
| `sprint_node.py` | `MeshNode`, CBOR codec, proof stub, CRDT merge |
| `test_sprint.py` | Tests for CBOR, proofs, partition and convergence under loss |
| `demo.py` | 4-node chaos demo: partition, heal, Sybil injection |

```bash
python demo.py
python -c "import test_sprint as t; [getattr(t,n)() for n in dir(t) if n.startswith('test_')]"
node tests/api.test.js
```

## 🚀 Run and deploy

```bash
python -m http.server -d public 3000   # local preview
vercel --prod                          # deploy, no build step
```

`api/node.js` is a Vercel serverless function (`POST {action: "verifyTx" | "verify" | "merge"}`) that re-verifies ECDSA transactions server-side.

## ⚠️ Honest limits

- Signatures prove **who authorised** a payment. This is **not** a zero-knowledge system.
- A double spend is resolved by a fixed tie-break rule, not true global ordering.
- The Python `verify_zk_proof` is a structural stub; swap in a real ZK-STARK verifier for production.
- Ledger state is not persisted; keys are generated fresh on each page load.

<div align="center">

**Built in a 6-hour sprint** 🔥 *Mesh. Prove. Converge. Survive.*

</div>
