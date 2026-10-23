"""6-hour sprint mesh node: CBOR over UDP, proof-stub verification, CRDT convergence, chaos drop."""
import hashlib
import random
import socket
import struct
import threading
import time


# ---- minimal CBOR (ints, str, bytes, list, dict, bool, None) ----
def _head(major: int, n: int) -> bytes:
    if n < 24:
        return bytes([major << 5 | n])
    for ai, fmt in ((24, ">B"), (25, ">H"), (26, ">I"), (27, ">Q")):
        if n < 1 << (8 * struct.calcsize(fmt)):
            return bytes([major << 5 | ai]) + struct.pack(fmt, n)
    raise ValueError("integer too large")


def cbor_encode(o) -> bytes:
    if o is None:
        return b"\xf6"
    if o is True:
        return b"\xf5"
    if o is False:
        return b"\xf4"
    if isinstance(o, int):
        return _head(0, o) if o >= 0 else _head(1, -1 - o)
    if isinstance(o, bytes):
        return _head(2, len(o)) + o
    if isinstance(o, str):
        b = o.encode()
        return _head(3, len(b)) + b
    if isinstance(o, (list, tuple)):
        return _head(4, len(o)) + b"".join(cbor_encode(x) for x in o)
    if isinstance(o, dict):
        return _head(5, len(o)) + b"".join(cbor_encode(k) + cbor_encode(v) for k, v in o.items())
    raise TypeError(type(o))


def _dec(b: bytes, i: int, depth: int = 0):
    if depth > 32:
        raise ValueError("too deep")
    ib = b[i]
    major, ai = ib >> 5, ib & 31
    i += 1
    if major == 7:
        if ai in (20, 21, 22):
            return {20: False, 21: True, 22: None}[ai], i
        raise ValueError("unsupported")
    if ai < 24:
        n = ai
    elif ai in (24, 25, 26, 27):
        size = 1 << (ai - 24)
        if i + size > len(b):
            raise ValueError("truncated")
        n = int.from_bytes(b[i:i + size], "big")
        i += size
    else:
        raise ValueError("unsupported")
    if major == 0:
        return n, i
    if major == 1:
        return -1 - n, i
    if major in (2, 3):
        if i + n > len(b):
            raise ValueError("truncated")
        raw = b[i:i + n]
        return (raw if major == 2 else raw.decode()), i + n
    if major == 4:
        out = []
        for _ in range(n):
            v, i = _dec(b, i, depth + 1)
            out.append(v)
        return out, i
    if major == 5:
        out = {}
        for _ in range(n):
            k, i = _dec(b, i, depth + 1)
            v, i = _dec(b, i, depth + 1)
            out[k] = v
        return out, i
    raise ValueError("unsupported")


def cbor_decode(b: bytes):
    v, i = _dec(b, 0)
    if i != len(b):
        raise ValueError("trailing bytes")
    return v


def proof_hash(sender: str, receiver: str, amount: int, nonce: int) -> str:
    return hashlib.sha256(f"{sender}|{receiver}|{amount}|{nonce}".encode()).hexdigest()


class MeshNode:
    DROP_RATE = 0.0  # set to 0.80 for chaos testing

    def __init__(self, node_id: str, port: int, peers=None, drop_rate: float = 0.0, trusted=None):
        self.node_id = node_id
        # Sybil defense: only writers in this set are accepted (None = open mesh)
        self.trusted = set(trusted) | {node_id} if trusted is not None else None
        self.port = port
        self.peers = list(peers or [])  # [(host, port)]
        self.drop_rate = drop_rate
        # per-account LWW register: name -> [balance, lamport, writer]
        self.ledger = {"alice": [500, 0, ""], "bob": [100, 0, ""]}
        self.vector_clock = {node_id: 0}
        self.lamport = 0
        self.seen_nonces = set()
        self.lock = threading.RLock()
        self.sock = None
        self.running = False

    @property
    def ledger_state(self):
        with self.lock:
            return {k: v[0] for k, v in self.ledger.items()}

    # ---- proof verification (structural stub; swap in a STARK verifier here) ----
    def verify_zk_proof(self, p) -> bool:
        try:
            if not isinstance(p, dict):
                return False
            s, r, a, n, h = (p.get(k) for k in ("sender", "receiver", "amount", "nonce", "proof_hash"))
            if not (isinstance(s, str) and isinstance(r, str) and isinstance(h, str)):
                return False
            if isinstance(a, bool) or isinstance(n, bool) or not isinstance(a, int) or not isinstance(n, int):
                return False
            if a <= 0 or s == r or n in self.seen_nonces:
                return False
            return h == proof_hash(s, r, a, n)
        except Exception:
            return False

    def make_transfer(self, sender: str, receiver: str, amount: int):
        nonce = random.getrandbits(48)
        return {"sender": sender, "receiver": receiver, "amount": amount, "nonce": nonce,
                "proof_hash": proof_hash(sender, receiver, amount, nonce)}

    def apply_transfer(self, p) -> bool:
        with self.lock:
            if not self.verify_zk_proof(p):
                return False
            bal = self.ledger.get(p["sender"], [0, 0, ""])[0]
            if bal < p["amount"]:
                return False
            self.seen_nonces.add(p["nonce"])
            self.vector_clock[self.node_id] = self.vector_clock.get(self.node_id, 0) + 1
            self.lamport += 1
            for acct, delta in ((p["sender"], -p["amount"]), (p["receiver"], p["amount"])):
                cur = self.ledger.get(acct, [0, 0, ""])[0]
                self.ledger[acct] = [cur + delta, self.lamport, self.node_id]
            return True

    # ---- CRDT merge: per-key LWW with (lamport, writer) total order => commutative/idempotent ----
    def apply_crdt_merge(self, incoming_clock: dict, incoming_state: dict):
        with self.lock:
            for node, t in incoming_clock.items():
                if isinstance(t, int) and (self.trusted is None or node in self.trusted):
                    self.vector_clock[node] = max(self.vector_clock.get(node, 0), t)
            for user, entry in incoming_state.items():
                try:
                    bal, ts, writer = entry
                    if not (isinstance(bal, int) and isinstance(ts, int) and isinstance(writer, str)):
                        continue
                except (TypeError, ValueError):
                    continue
                if self.trusted is not None and writer and writer not in self.trusted:
                    continue
                cur = self.ledger.get(user)
                if cur is None or (ts, writer) > (cur[1], cur[2]):
                    self.ledger[user] = [bal, ts, writer]
                self.lamport = max(self.lamport, ts)

    def snapshot(self) -> bytes:
        with self.lock:
            return cbor_encode({"t": "sync", "from": self.node_id, "clock": self.vector_clock,
                                "state": self.ledger})

    def simulate_packet_drop(self, payload: bytes = b"") -> bool:
        """True if packet survives."""
        return random.random() >= self.drop_rate

    # ---- networking ----
    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", self.port))
        self.sock.settimeout(0.1)
        self.running = True
        threading.Thread(target=self._recv_loop, daemon=True).start()

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()

    def send(self, data: bytes, peer):
        if self.running and self.simulate_packet_drop(data):
            try:
                self.sock.sendto(data, peer)
            except OSError:
                pass

    def gossip(self):
        data = self.snapshot()
        for p in self.peers:
            self.send(data, p)

    def _recv_loop(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                return
            try:
                msg = cbor_decode(data)
                if isinstance(msg, dict) and msg.get("t") == "sync":
                    self.apply_crdt_merge(msg.get("clock", {}), msg.get("state", {}))
            except Exception:
                pass  # malformed packets must never crash the node


if __name__ == "__main__":
    node = MeshNode("node_alpha", 8080)
    print(f"[{node.node_id}] Initialized ledger state: {node.ledger_state}")
