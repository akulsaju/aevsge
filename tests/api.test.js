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
