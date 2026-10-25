// Ear Bench tuning math: scale model, degree -> cents, nearest-pitch mapping,
// and the proportional / subcontrary triad finder. Pure functions, no DOM.
"use strict";

const Tuning = (() => {
  const centsOf = (ratio) => 1200 * Math.log2(ratio);

  // A bundle scale -> {tones: cents of one period from 1/1, period}.
  // Scala lists every degree but 1/1, and its last line is the period.
  function model(scale) {
    const listed = scale.cents;
    const period = listed[listed.length - 1];
    const tones = [0, ...listed.slice(0, -1)].sort((a, b) => a - b);
    return { tones, period, n: tones.length };
  }

  // Degree d (any integer, 0 = 1/1) -> absolute cents above 1/1.
  function degreeCents(m, d) {
    const oct = Math.floor(d / m.n);
    const idx = d - oct * m.n;
    return oct * m.period + m.tones[idx];
  }

  // Absolute cents -> the degree of m whose pitch is closest.
  function nearestDegree(m, cents) {
    const oct = Math.floor(cents / m.period);
    let best = 0;
    let bestErr = Infinity;
    for (let o = oct - 1; o <= oct + 1; o++) {
      for (let i = 0; i < m.n; i++) {
        const err = Math.abs(o * m.period + m.tones[i] - cents);
        if (err < bestErr) { bestErr = err; best = o * m.n + i; }
      }
    }
    return best;
  }

  function gcd(a, b) { return b ? gcd(b, a % b) : Math.abs(a); }

  // Best p/q (q <= maxQ) for a frequency ratio, if within tolCents.
  function approxRatio(r, maxQ = 24, tolCents = 4) {
    let best = null;
    for (let q = 1; q <= maxQ; q++) {
      const p = Math.round(r * q);
      if (p <= 0) continue;
      const err = Math.abs(centsOf(p / q) - centsOf(r));
      if (err <= tolCents && (!best || err < best.err - 1e-9)) best = { p, q, err };
    }
    return best;
  }

  // Integer form of a triad on outer ratio r: P = 2q:(q+p):2p, S = q(q+p):2pq:p(q+p).
  function integerForm(kind, r) {
    const a = approxRatio(r);
    if (!a) return null;
    const { p, q } = a;
    const parts = kind === "P" ? [2 * q, q + p, 2 * p] : [q * (q + p), 2 * p * q, p * (q + p)];
    const g = parts.reduce(gcd);
    return parts.map((x) => x / g).join(":");
  }

  // Every triad (a, b, c) with root a in the first period and c within one
  // period above it, whose middle tone lies within tolCents of the
  // arithmetic (P) or harmonic (S) mean of the outer frequencies.
  function findTriads(m, tolCents) {
    const ext = [];
    for (let o = 0; o <= 1; o++) {
      for (let i = 0; i < m.n; i++) ext.push({ d: o * m.n + i, c: o * m.period + m.tones[i] });
    }
    ext.push({ d: 2 * m.n, c: 2 * m.period });
    const out = [];
    for (let ia = 0; ia < m.n; ia++) {
      const A = ext[ia];
      for (let ic = ia + 2; ic < ext.length && ext[ic].c - A.c <= m.period + 1e-9; ic++) {
        const C = ext[ic];
        const r = Math.pow(2, (C.c - A.c) / 1200);
        const targets = { P: (1 + r) / 2, S: (2 * r) / (1 + r) };
        for (const kind of ["P", "S"]) {
          const tc = A.c + centsOf(targets[kind]);
          let best = null;
          for (let ib = ia + 1; ib < ic; ib++) {
            const dev = ext[ib].c - tc;
            if (!best || Math.abs(dev) < Math.abs(best.dev)) best = { B: ext[ib], dev };
          }
          if (best && Math.abs(best.dev) <= tolCents) {
            out.push({
              kind,
              degrees: [A.d, best.B.d, C.d],
              cents: [A.c, best.B.c, C.c],
              dev: best.dev,
              form: integerForm(kind, r),
            });
          }
        }
      }
    }
    return out.sort((x, y) => Math.abs(x.dev) - Math.abs(y.dev));
  }

  function stepSizes(m) {
    return m.tones.map((t, i) => (i + 1 < m.n ? m.tones[i + 1] : m.period) - t);
  }

  // Place a JI reference inside a chain: try every transposition that puts a
  // reference tone on a chain tone, keep the one whose tones land closest
  // (errors capped at 30c, so a chain that holds only part of the reference
  // still aligns on the part it holds).
  function alignReference(chain, ref) {
    let best = null;
    for (const t of chain.tones) {
      for (const r of ref.tones) {
        const off = t - r;
        let score = 0;
        let worst = 0;
        for (const rc of ref.tones) {
          const c = rc + off;
          const err = Math.abs(degreeCents(chain, nearestDegree(chain, c)) - c);
          score += Math.min(err, 30);
          worst = Math.max(worst, err);
        }
        if (!best || score < best.score - 1e-9) best = { off, score, worst };
      }
    }
    return best;
  }

  // The reference's exact triads, re-voiced on the nearest chain tones.
  // dev: how far the chain's middle tone sits from the outer tones' mean;
  // toneErr: the worst of the three chain tones against JI.
  function targetTriads(chain, ref, align) {
    return findTriads(ref, 0.01).map((tr) => {
      const ji = tr.cents.map((c) => c + align.off);
      const degrees = ji.map((c) => nearestDegree(chain, c));
      const cents = degrees.map((d) => degreeCents(chain, d));
      const r = Math.pow(2, (cents[2] - cents[0]) / 1200);
      const mean = tr.kind === "P" ? (1 + r) / 2 : (2 * r) / (1 + r);
      return {
        kind: tr.kind, form: tr.form, ji, degrees, cents,
        dev: cents[1] - (cents[0] + centsOf(mean)),
        toneErr: Math.max(...cents.map((c, i) => Math.abs(c - ji[i]))),
      };
    }).sort((x, y) => Math.abs(x.dev) - Math.abs(y.dev));
  }

  return { centsOf, model, degreeCents, nearestDegree, approxRatio, integerForm, findTriads, stepSizes, alignReference, targetTriads };
})();

if (typeof module !== "undefined") module.exports = Tuning;
