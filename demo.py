"""Chaos demo: 4-node mesh, 80% packet loss, partition + heal, Sybil injection."""
import socket
import time

from sprint_node import MeshNode, cbor_encode

BASE = 19000
IDS = ["n1", "n2", "n3", "n4"]


def main():
    ports = {i: BASE + k for k, i in enumerate(IDS)}
    nodes = {i: MeshNode(i, ports[i], drop_rate=0.8, trusted=IDS) for i in IDS}
    full = {i: [("127.0.0.1", ports[j]) for j in IDS if j != i] for i in IDS}
    for i, n in nodes.items():
        n.peers = full[i]
        n.start()

    def gossip_until(cond, timeout=15):
        end = time.time() + timeout
        while time.time() < end:
            for n in nodes.values():
                n.gossip()
            if cond():
                return True
            time.sleep(0.05)
        return False

    def agree():
        return len({tuple(sorted(n.ledger_state.items())) for n in nodes.values()}) == 1

    print("Partition: {n1,n2} | {n3,n4}")
    for i in IDS:
        nodes[i].peers = [p for p in full[i] if (p[1] - BASE < 2) == (ports[i] - BASE < 2)]
    assert nodes["n1"].apply_transfer(nodes["n1"].make_transfer("alice", "bob", 100))
    time.sleep(0.1)
    gossip_until(lambda: False, 1)
    print("  during partition agree =", agree())

    print("Heal partition (80% loss still active)")
    for i in IDS:
        nodes[i].peers = full[i]
    print("  converged =", gossip_until(agree), nodes["n4"].ledger_state)

    print("Sybil injection: untrusted node forges a rich ledger")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    evil = cbor_encode({"t": "sync", "from": "sybil", "clock": {"sybil": 99},
                        "state": {"alice": [10 ** 9, 10 ** 6, "sybil"]}})
    for _ in range(50):
        for p in ports.values():
            s.sendto(evil, ("127.0.0.1", p))
    time.sleep(0.5)
    print("  poisoned =", any(n.ledger_state["alice"] > 10 ** 6 for n in nodes.values()))
    print("  final ledger:", nodes["n1"].ledger_state)

    for n in nodes.values():
        n.stop()


if __name__ == "__main__":
    main()
