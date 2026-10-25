// Ear Bench generator math: given a generator chosen up front and any
// combination product set, how well does the CPS sit on that generator's
// MOS levels? Pure functions, no DOM; tested in experiments/ear_bench/tests.
//
// What carries over from the experiments (see JUDGING.md, LOG.md):
//   - triads first: a level is ranked by how many of the structure's exact
//     triads it holds (the count objective, CPSFIT-003 / G-032); melody facts
//     are reported and only break ties, because melody is forgiving (G-031);
//   - bands: 2c is the registered LOCK tier; 5c and 10c are listening bands
//     from G-029 (5-7c passed under the electric piano), provisional until
//     EAR-eps (G-025) measures them;
//   - the tone cap: a tone counts as present only within 20c, and a triad
//     only when all three of its tones are present (SUBFIT: never drop it);
//   - window and transposition both float (G-032's open "floating origin");
//   - single val: each placement says whether one generator count per seed
//     explains every tone (homomorphic, SUBFIT-002);
//   - nobility says nothing about harmony: nothing here ranks by complexity.
"use strict";

const Generator = (() => {
  const T = typeof Tuning !== "undefined" ? Tuning : require("./tuning.js");
  const CAP = 20;
  const BANDS = [2, 5, 10];
  const wrapC = (c) => ((((c + 600) % 1200) + 1200) % 1200) - 600;

  // Every N up to maxN whose chain of N generators has at most two step sizes.
  function mosLevels(g, maxN = 130) {
    const out = [];
    for (let n = 2; n <= maxN; n++) {
      const pcs = Array.from({ length: n }, (_, k) => (k * g) % 1).sort((a, b) => a - b);
      const steps = pcs.map((p, i) => (i + 1 < n ? pcs[i + 1] : 1) - p);
      const sizes = [];
      steps.forEach((s) => { if (!sizes.some((x) => Math.abs(x - s) < 1e-9)) sizes.push(s); });
      if (sizes.length <= 2) {
        const large = Math.max(...sizes) * 1200;
        const small = Math.min(...sizes) * 1200;
        out.push({ n, large, small, ratio: small > 0 ? large / small : 1 });
      }
    }
    return out;
  }

  // Odd-prime exponents of an integer (the octave is the period, so 2 is dropped).
  function monzo(x) {
    const out = {};
    let v = Math.round(x);
    while (v % 2 === 0 && v > 1) v /= 2;
    for (let p = 3; p * p <= v; p += 2) while (v % p === 0) { out[p] = (out[p] || 0) + 1; v /= p; }
    if (v > 1) out[v] = (out[v] || 0) + 1;
    return out;
  }

  // A structure: its tones in cents (sorted, from 0) with each tone's odd-prime
  // exponents (null for a structure given as a plain scale), and its exact
  // proportional and subcontrary triads.
  function finish(name, raw) {
    const sorted = [...raw].sort((a, b) => a.cents - b.cents);
    const base = sorted[0].cents;
    const tones = [];
    sorted.forEach((t) => {
      const c = t.cents - base;
      if (!tones.some((u) => Math.abs(u.cents - c) < 1e-6)) tones.push({ cents: c, factors: t.factors, monzo: t.monzo || null });
    });
    const model = T.model({ cents: [...tones.slice(1).map((t) => t.cents), 1200] });
    return { name, tones, model, triads: T.findTriads(model, 0.01) };
  }

  function cps(seeds, k) {
    const combos = [];
    const pick = (start, chosen) => {
      if (chosen.length === k) { combos.push(chosen); return; }
      for (let i = start; i < seeds.length; i++) pick(i + 1, [...chosen, i]);
    };
    pick(0, []);
    const raw = combos.map((idx) => {
      const prod = idx.reduce((p, i) => p * seeds[i], 1);
      return { cents: ((1200 * Math.log2(prod)) % 1200 + 1200) % 1200, factors: idx, monzo: monzo(prod) };
    });
    return finish(`CPS(${seeds.length},${k}) ${seeds.join("·")}`, raw);
  }

  function fromScale(scale) {
    return finish(scale.name, [0, ...scale.cents.slice(0, -1)].map((c) => ({ cents: c % 1200, factors: null })));
  }

  // Place the structure on the N-note chain of g: choose the window of N
  // consecutive chain positions and the transposition that keep the most
  // tones within the cap, then the smallest worst tone error.
  function place(g, n, structure, cap = CAP) {
    const tones = structure.tones;
    const span = 2 * n;
    const cand = tones.map((t) => {
      const list = [];
      for (let k = -span; k <= span; k++) {
        const r = wrapC(1200 * k * g - t.cents);
        if (Math.abs(r) <= cap * 2) list.push({ k, r });
      }
      return list;
    });
    let best = null;
    for (let w = -span; w <= span - n + 1; w++) {
      const choice = cand.map((list) => {
        let pickC = null;
        list.forEach((c) => { if (c.k >= w && c.k < w + n && (!pickC || Math.abs(c.r) < Math.abs(pickC.r))) pickC = c; });
        return pickC;
      });
      // Float the transposition: centre the residuals of the tones found.
      const found = choice.filter(Boolean);
      if (!found.length) continue;
      const shift = (Math.max(...found.map((c) => c.r)) + Math.min(...found.map((c) => c.r))) / 2;
      const res = choice.map((c) => (c ? c.r - shift : null));
      const present = res.filter((r) => r !== null && Math.abs(r) <= cap).length;
      const worst = Math.max(...res.filter((r) => r !== null && Math.abs(r) <= cap).map(Math.abs), 0);
      if (!best || present > best.present || (present === best.present && worst < best.worst - 1e-9)) {
        best = { n, window: w, k: choice.map((c) => (c ? c.k : null)), res, present, worst };
      }
    }
    if (!best) return { n, window: null, k: tones.map(() => null), res: tones.map(() => null), present: 0, worst: null };
    const res = best.res.map((r) => (r !== null && Math.abs(r) <= cap ? r : null));
    return { ...best, res, k: best.k.map((k, i) => (res[i] === null ? null : k)) };
  }

  // Each exact triad of the structure as the chain plays it: present only if
  // all three tones are; dev is the middle tone's distance from the outer
  // tones' arithmetic (P) or harmonic (S) mean, as everywhere on the bench.
  function triads(structure, placement) {
    const n = structure.model.n;
    return structure.triads.map((tr) => {
      const idx = tr.degrees.map((d) => ((d % n) + n) % n);
      if (idx.some((i) => placement.res[i] === null)) return { kind: tr.kind, form: tr.form, tones: idx, present: false, dev: null };
      const cents = tr.degrees.map((d, j) => tr.cents[j] + placement.res[idx[j]]);
      const r = Math.pow(2, (cents[2] - cents[0]) / 1200);
      const mean = tr.kind === "P" ? (1 + r) / 2 : (2 * r) / (1 + r);
      return { kind: tr.kind, form: tr.form, tones: idx, present: true, dev: cents[1] - (cents[0] + T.centsOf(mean)), cents };
    });
  }

  // One generator count per odd prime (plus a shared offset) explains every
  // present tone's chain position: the placement is a single val, a
  // temperament (SUBFIT-002's "homomorphic"). Seeds are not independent:
  // 9 must cost exactly twice 3.
  function singleVal(structure, placement) {
    const rows = structure.tones.map((t, i) => ({ m: t.monzo, k: placement.k[i] })).filter((r) => r.m && r.k !== null);
    if (!rows.length || !structure.tones[0].monzo) return null;
    const primes = [...new Set(rows.flatMap((r) => Object.keys(r.m).map(Number)))].sort((a, b) => a - b);
    const m = primes.length + 1;
    const A = rows.map((r) => [...primes.map((p) => r.m[p] || 0), 1]);
    const ata = Array.from({ length: m }, (_, i) => Array.from({ length: m }, (_, j) => A.reduce((s, a) => s + a[i] * a[j], 0) + (i === j ? 1e-9 : 0)));
    const atb = Array.from({ length: m }, (_, i) => A.reduce((s, a, r) => s + a[i] * rows[r].k, 0));
    const x = solve(ata, atb);
    if (!x) return false;
    // The offset absorbs the shared shift; check that integer prime counts fit exactly.
    const v = x.slice(0, -1).map(Math.round);
    const offs = rows.map((r, i) => r.k - A[i].slice(0, -1).reduce((s, a, j) => s + a * v[j], 0));
    return offs.every((o) => o === offs[0]);
  }

  function solve(M, b) {
    const n = b.length;
    const a = M.map((row, i) => [...row, b[i]]);
    for (let c = 0; c < n; c++) {
      let p = c;
      for (let r = c + 1; r < n; r++) if (Math.abs(a[r][c]) > Math.abs(a[p][c])) p = r;
      if (Math.abs(a[p][c]) < 1e-12) return null;
      [a[c], a[p]] = [a[p], a[c]];
      for (let r = 0; r < n; r++) {
        if (r === c) continue;
        const f = a[r][c] / a[c][c];
        for (let j = c; j <= n; j++) a[r][j] -= f * a[c][j];
      }
    }
    return a.map((row, i) => row[n] / row[i]);
  }

  // The match profile of one generator for one structure, level by level.
  function profile(g, structure, { minN, maxN = 120 } = {}) {
    const lo = minN || structure.tones.length;
    return mosLevels(g, maxN).filter((l) => l.n >= lo).map((level) => {
      const placement = place(g, level.n, structure);
      const tri = triads(structure, placement);
      const present = tri.filter((t) => t.present);
      const held = BANDS.map((b) => present.filter((t) => Math.abs(t.dev) <= b).length);
      return {
        ...level, placement, tones: placement.present, totalTones: structure.tones.length,
        held, totalTriads: tri.length, worstTone: placement.worst,
        worstTriad: present.length ? Math.max(...present.map((t) => Math.abs(t.dev))) : null,
        singleVal: singleVal(structure, placement),
      };
    });
  }

  // The chain itself as a playable scale (one period, cents from the window's
  // first position), with the structure's transposition carried in `shift`.
  function chainScale(g, placement) {
    const cents = Array.from({ length: placement.n }, (_, i) => ((1200 * (placement.window + i) * g) % 1200 + 1200) % 1200);
    const sorted = [...cents].sort((a, b) => a - b);
    const base = sorted[0];
    return [...sorted.slice(1).map((c) => c - base), 1200];
  }

  return { CAP, BANDS, mosLevels, cps, fromScale, place, triads, singleVal, profile, chainScale };
})();

if (typeof module !== "undefined") module.exports = Generator;
