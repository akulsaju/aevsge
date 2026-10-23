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
  if (body.action === "merge")
    return res.status(200).end(JSON.stringify({ state: merge(body.a || {}, body.b || {}) }));
  res.status(400).end(JSON.stringify({ error: "unknown action" }));
};
module.exports.verify = verify;
module.exports.merge = merge;
