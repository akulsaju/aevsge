const assert = require("assert");
const crypto = require("crypto");
const h = require("../api/node");

const hash = (s, r, a, n) => crypto.createHash("sha256").update(`${s}|${r}|${a}|${n}`).digest("hex");
const good = { sender: "alice", receiver: "bob", amount: 5, nonce: 7, proof_hash: hash("alice", "bob", 5, 7) };

assert.strictEqual(h.verify(good).valid, true);
assert.strictEqual(h.verify({ ...good, amount: 6 }).valid, false);
assert.strictEqual(h.verify(null).valid, false);
assert.strictEqual(h.verify({ ...good, amount: -1 }).valid, false);

const a = { alice: [10, 1, "n1"] }, b = { alice: [20, 2, "n2"], bob: [1, 1, "n2"] };
assert.deepStrictEqual(h.merge(a, b), h.merge(b, a));
assert.deepStrictEqual(h.merge(h.merge(a, b), b), h.merge(a, b));
assert.deepStrictEqual(h.merge(a, { alice: "junk" }), a);

// ECDSA transaction verification (signature format matches WebCrypto: IEEE P1363)
function signedTx(amount, signer) {
  const mk = () => crypto.generateKeyPairSync("ec", { namedCurve: "P-256" });
  const a = mk(), m = signer || a;
  const j = a.publicKey.export({ format: "jwk" });
  const pub = { kty: j.kty, crv: j.crv, x: j.x, y: j.y };
  const from = crypto.createHash("sha256").update(pub.x + "." + pub.y).digest("hex").slice(0, 16);
  const t = { from, to: "bob", amount, seq: 1, lamport: 1, pub };
  const msg = `${t.from}|${t.to}|${t.amount}|${t.seq}|${t.lamport}`;
  t.sig = crypto.sign("sha256", Buffer.from(msg), { key: m.privateKey, dsaEncoding: "ieee-p1363" }).toString("hex");
  t.id = crypto.createHash("sha256").update(msg + t.sig).digest("hex").slice(0, 16);
  return t;
}
const stx = signedTx(10);
assert.strictEqual(h.verifyTx(stx).valid, true);
assert.strictEqual(h.verifyTx({ ...stx, amount: 11 }).valid, false);
assert.strictEqual(h.verifyTx(signedTx(10, crypto.generateKeyPairSync("ec", { namedCurve: "P-256" }))).reason, "bad signature");
assert.strictEqual(h.verifyTx(null).valid, false);
assert.strictEqual(h.verifyTx({ ...stx, id: "0000000000000000" }).reason, "wrong transaction id");

function call(body, method = "POST") {
  return new Promise((ok) => {
    const res = { setHeader() {}, status(c) { this.code = c; return this; }, end(t) { ok({ code: this.code, body: JSON.parse(t) }); } };
    h({ method, body }, res);
  });
}
(async () => {
  assert.strictEqual((await call({ action: "verify", proof: good })).body.valid, true);
  assert.strictEqual((await call({}, "GET")).code, 405);
  assert.strictEqual((await call({ action: "x" })).code, 400);
  assert.strictEqual((await call("{bad")).code, 400);
  console.log("api tests passed");
})();
