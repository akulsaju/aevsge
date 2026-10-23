import random
import time

from sprint_node import MeshNode, cbor_decode, cbor_encode


def wait(cond, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.05)
    return False


def test_cbor_roundtrip():
    o = {"a": [1, -5, 70000, "x", b"y", None, True], "b": {"c": 2 ** 40}}
    assert cbor_decode(cbor_encode(o)) == o


def test_proof_accept_reject():
    n = MeshNode("n", 0)
    good = n.make_transfer("alice", "bob", 50)
    assert n.verify_zk_proof(good)
    bad = dict(good, amount=51)
    assert not n.verify_zk_proof(bad)
    assert not n.verify_zk_proof({"proof_hash": "x"})
    assert not n.verify_zk_proof("junk")
    assert n.apply_transfer(good) and not n.apply_transfer(good)  # replay rejected
    assert not n.apply_transfer(n.make_transfer("alice", "bob", 10 ** 6))  # overdraft


def test_partition_and_converge_under_80pct_loss():
    random.seed(1)
    a = MeshNode("a", 18081, [("127.0.0.1", 18082)], drop_rate=0.8)
    b = MeshNode("b", 18082, [("127.0.0.1", 18081)], drop_rate=0.8)
    a.start(); b.start()
    try:
        # partition: independent writes on different accounts
        assert a.apply_transfer(a.make_transfer("alice", "bob", 100))
        assert b.apply_transfer(b.make_transfer("carol", "dave", 0 + 1)) is False  # no funds
        for _ in range(3):
            a.gossip(); b.gossip()
        # reconnect: gossip repeatedly through lossy link
        def converged():
            a.gossip(); b.gossip()
            return a.ledger_state == b.ledger_state and a.ledger_state["bob"] == 200
        assert wait(converged)
        # garbage packets must not crash
        a.sock.sendto(b"\xff\x00garbage", ("127.0.0.1", 18082))
        time.sleep(0.2)
        assert b.running
    finally:
        a.stop(); b.stop()


def test_merge_idempotent_commutative():
    x, y = MeshNode("x", 0), MeshNode("y", 0)
    x.apply_transfer(x.make_transfer("alice", "bob", 10))
    y.apply_transfer(y.make_transfer("bob", "alice", 5))
    for n, o in ((x, y), (y, x)):
        n.apply_crdt_merge(o.vector_clock, o.ledger)
        n.apply_crdt_merge(o.vector_clock, o.ledger)
    assert x.ledger_state == y.ledger_state
