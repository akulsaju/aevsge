// Stateless mesh-node API for Vercel: POST {action:"verify"|"merge", ...}
const crypto = require("crypto");

const hash = (s, r, a, n) =>
  crypto.createHash("sha256").update(`${s}|${r}|${a}|${n}`).digest("hex");

function verify(p) {
  if (!p || typeof p !== "object") return { valid: false, reason: "not an object" };
  const { sender: s, receiver: r, amount: a, nonce: n, proof_hash: h } = p;
  if (typeof s !== "string" || typeof r !== "string" || typeof h !== "string")
    return { valid: false, reason: "bad field types" };
  if (!Number.isSafeInteger(a) || !Number.isSafeInteger(n) || a <= 0)
    return { valid: false, reason: "bad amount/nonce" };
  if (s === r) return { valid: false, reason: "self transfer" };
  if (h !== hash(s, r, a, n)) return { valid: false, reason: "proof hash mismatch" };
  return { valid: true };
}

// Verifies a P-256 ECDSA-signed transaction exactly as the browser demo does
function verifyTx(t) {
  try {
    if (!t || typeof t !== "object") return { valid: false, reason: "not an object" };
    const { from, to, amount, seq, lamport, pub, sig, id } = t;
    if (typeof from !== "string" || typeof to !== "string" || from === to || to.length > 64)
      return { valid: false, reason: "malformed" };
    if (![amount, seq, lamport].every(Number.isSafeInteger) || amount <= 0 || seq < 1 || lamport < 0)
      return { valid: false, reason: "malformed" };
    if (!pub || typeof pub.x !== "string" || typeof pub.y !== "string" || !/^[0-9a-f]{128}$/.test(sig || ""))
      return { valid: false, reason: "malformed" };
    const acct = crypto.createHash("sha256").update(pub.x + "." + pub.y).digest("hex").slice(0, 16);
    if (acct !== from) return { valid: false, reason: "key does not belong to sender" };
    const msg = `${from}|${to}|${amount}|${seq}|${lamport}`;
    const key = crypto.createPublicKey({ key: { kty: "EC", crv: "P-256", x: pub.x, y: pub.y }, format: "jwk" });
    if (!crypto.verify("sha256", Buffer.from(msg), { key, dsaEncoding: "ieee-p1363" }, Buffer.from(sig, "hex")))
      return { valid: false, reason: "bad signature" };
    if (crypto.createHash("sha256").update(msg + sig).digest("hex").slice(0, 16) !== id)
      return { valid: false, reason: "wrong transaction id" };
    return { valid: true };
  } catch {
    return { valid: false, reason: "malformed" };
  }
}

// LWW per key ordered by (lamport, writer); commutative + idempotent
function merge(a, b) {
  const out = { ...a };
  for (const [k, v] of Object.entries(b || {})) {
    if (!Array.isArray(v) || v.length !== 3) continue;
    const [bal, ts, w] = v;
    if (!Number.isSafeInteger(bal) || !Number.isSafeInteger(ts) || typeof w !== "string") continue;
    const cur = out[k];
    if (!cur || ts > cur[1] || (ts === cur[1] && w > cur[2])) out[k] = [bal, ts, w];
  }
  return out;
}

module.exports = (req, res) => {
  res.setHeader("Content-Type", "application/json");
  if (req.method !== "POST") return res.status(405).end(JSON.stringify({ error: "POST only" }));
  let body = req.body;
  if (typeof body === "string") {
    try { body = JSON.parse(body); } catch { return res.status(400).end(JSON.stringify({ error: "bad json" })); }
  }
  if (!body || typeof body !== "object") return res.status(400).end(JSON.stringify({ error: "bad body" }));
  if (body.action === "verify") return res.status(200).end(JSON.stringify(verify(body.proof)));
  if (body.action === "verifyTx") return res.status(200).end(JSON.stringify(verifyTx(body.tx)));
  if (body.action === "merge")
    return res.status(200).end(JSON.stringify({ state: merge(body.a || {}, body.b || {}) }));
  res.status(400).end(JSON.stringify({ error: "unknown action" }));
};
module.exports.verify = verify;
module.exports.verifyTx = verifyTx;
module.exports.merge = merge;
