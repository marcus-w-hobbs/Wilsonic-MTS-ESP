// Crossroads engine: just-intonation structures (CPS, Euler genus), their
// subsets, and the GAPFILL-001 gap-filling methods, ported from
// experiments/lattice/gapfill001.py (v1.0.1) with its helpers (dynmos001,
// meru001, cpsfit001/002, gold002). Scores mirror the frozen triad scorer's
// tempered path (v1.1.0, 2 cents, middle-anchored, degeneracy guard) and the
// frozen melodic scorer (v0.1.0: M1 gap classes, M2 constant structure,
// M3 propriety). Runs in the browser (window.Engine) and in Node (tests).
"use strict";

(function (root) {
  const CENTS = 1200;

  // ---------------------------------------------------------------- rationals
  // A rational is [n, d] of BigInt, reduced, d > 0, n > 0 for pitches.
  const gcd = (a, b) => { a = a < 0n ? -a : a; b = b < 0n ? -b : b; while (b) [a, b] = [b, a % b]; return a; };
  const R = (n, d = 1n) => { n = BigInt(n); d = BigInt(d); if (d < 0n) { n = -n; d = -d; } const g = gcd(n, d) || 1n; return [n / g, d / g]; };
  const mul = (x, y) => R(x[0] * y[0], x[1] * y[1]);
  const div = (x, y) => R(x[0] * y[1], x[1] * y[0]);
  const add = (x, y) => R(x[0] * y[1] + y[0] * x[1], x[1] * y[1]);
  const cmp = (x, y) => { const l = x[0] * y[1], r = y[0] * x[1]; return l < r ? -1 : l > r ? 1 : 0; };
  const eq = (x, y) => x[0] === y[0] && x[1] === y[1];
  const key = (x) => `${x[0]}/${x[1]}`;
  const str = (x) => (x[1] === 1n ? `${x[0]}` : `${x[0]}/${x[1]}`);
  const ONE = R(1), TWO = R(2);

  function log2Big(n) {
    const bits = n.toString(2).length;
    if (bits <= 52) return Math.log2(Number(n));
    const shift = BigInt(bits - 53);
    return Math.log2(Number(n >> shift)) + Number(shift);
  }
  // Python's cents_of is 1200 * log2(float(Fraction)); match it when both parts fit a double.
  const SAFE = 2n ** 53n;
  const log2R = (x) => (x[0] < SAFE && x[1] < SAFE ? Math.log2(Number(x[0]) / Number(x[1])) : log2Big(x[0]) - log2Big(x[1]));
  const centsOf = (x) => CENTS * log2R(x);
  const tenney = (x) => log2Big(x[0]) + log2Big(x[1]);
  const mod = (a, m) => { const r = a % m; return r < 0 ? r + m : r; };   // exact like Python % for m > 0

  function red(x) {
    let [n, d] = x;
    while (n >= 2n * d) d *= 2n;
    while (n < d) n *= 2n;
    return R(n, d);
  }
  function uniqSorted(xs) {
    const seen = new Map();
    for (const x of xs) seen.set(key(x), x);
    return [...seen.values()].sort(cmp);
  }
  function maxPrime(x) {
    let best = 2n;
    for (let m of [x[0], x[1]]) {
      if (m.toString(2).length > 60) return null;      // too big to factor here
      for (let p = 2n; p * p <= m; p += (p === 2n ? 1n : 2n)) while (m % p === 0n) { if (p > best) best = p; m /= p; }
      if (m > best) best = m;
    }
    return Number(best);
  }

  // ---------------------------------------------------------------- structures
  function combos(arr, k) {
    const out = [];
    const rec = (start, pick) => {
      if (pick.length === k) { out.push(pick.slice()); return; }
      for (let i = start; i < arr.length; i++) { pick.push(arr[i]); rec(i + 1, pick); pick.pop(); }
    };
    rec(0, []);
    return out;
  }
  const prodR = (xs) => xs.reduce((acc, s) => mul(acc, R(s)), ONE);
  const cps = (seeds, k) => uniqSorted(combos(seeds, k).map((c) => red(prodR(c))));
  const genus = (seeds) => uniqSorted(Array.from({ length: seeds.length + 1 }, (_, k) => combos(seeds, k)).flat().map((c) => red(prodR(c))));
  // Sub-structure: fix seeds IN (always used) and OUT (never used); the rest
  // R form CPS(|R|, k - |IN|) multiplied by the product of IN.
  function subCps(seeds, k, inSeeds, outSeeds) {
    const rest = seeds.filter((s) => !inSeeds.includes(s) && !outSeeds.includes(s));
    const kk = k - inSeeds.length;
    if (kk < 0 || kk > rest.length) return [];
    const base = prodR(inSeeds);
    return uniqSorted(combos(rest, kk).map((c) => red(mul(base, prodR(c)))));
  }
  // The census order of subsetmel000.enumerate_subsets (hexanies + dekanies).
  function censusSubsets(seedsIn) {
    const seeds = seedsIn.slice().sort((a, b) => a - b);
    const out = [];
    for (const x of seeds) out.push({ name: `dekany_in[in=${x},out=none]`, kind: "dekany_in", inS: [x], outS: [] });
    for (const x of seeds) out.push({ name: `dekany_out[in=none,out=${x}]`, kind: "dekany_out", inS: [], outS: [x] });
    for (const x of seeds) for (const y of seeds) if (x !== y) out.push({ name: `hexany[in=${x},out=${y}]`, kind: "hexany", inS: [x], outS: [y] });
    return out.map((s) => ({ ...s, tones: subCps(seeds, 3, s.inS, s.outS) }));
  }

  // ---------------------------------------------------------------- scorers
  // Frozen triads v1.1.0 tempered path (score_cents_anchored), mirrored.
  function canonicalCents(cents, eps) {
    const r = cents.map((c) => mod(c, CENTS)).sort((a, b) => a - b);
    const out = [];
    for (const c of r) if (!out.length || c - out[out.length - 1] > eps) out.push(c);
    if (out.length > 1 && CENTS - out[out.length - 1] <= eps && out[0] <= eps) out.pop();
    return out;
  }
  function triads(cents, eps = 2.0, maxSpan = 1200, collect = false) {
    const scale = canonicalCents(cents, 1e-6);
    let P = 0, S = 0, G = 0;
    const list = [];
    for (const b of scale) {
      const lows = [], highs = [];
      for (const pc of scale) {
        const off = mod(pc - b, CENTS);
        if (off === 0) continue;
        lows.push(b - CENTS + off);
        highs.push(b + off);
      }
      for (const a of lows) for (const c of highs) {
        if (c - a > maxSpan) continue;
        const fa = 2 ** (a / CENTS), fb = 2 ** (b / CENTS), fc = 2 ** (c / CENTS);
        const p = Math.abs(CENTS * Math.log2((fa + fc) / (2 * fb))) < eps;
        const s = Math.abs(CENTS * Math.log2(fb * (fa + fc) / (2 * fa * fc))) < eps;
        const g = Math.abs(CENTS * Math.log2((fa * fc) / (fb * fb))) < eps;
        if (!p && !s && !g) continue;
        const am = (fa + fc) / 2, hm = 2 * fa * fc / (fa + fc);
        if (!(Math.abs(CENTS * Math.log2(am / hm)) >= eps)) continue;   // degeneracy guard
        if (p) { P++; if (collect) list.push({ kind: "P", a, b, c }); }
        if (s) { S++; if (collect) list.push({ kind: "S", a, b, c }); }
        if (g) G++;
      }
    }
    return { P, S, G, list };
  }
  // Frozen melodic v0.1.0, mirrored.
  function clusterSorted(values, eps) {
    const bounds = [];
    let start = 0;
    for (let i = 1; i < values.length; i++) if (values[i] - values[start] > eps) { bounds.push([start, i]); start = i; }
    if (values.length) bounds.push([start, values.length]);
    return bounds;
  }
  function melodic(cents) {
    const scale = canonicalCents(cents, 0.01);
    const n = scale.length;
    const gaps = scale.map((c, i) => (i < n - 1 ? scale[i + 1] - c : CENTS - scale[n - 1] + scale[0])).sort((a, b) => a - b);
    const gapClasses = clusterSorted(gaps, 0.5).length;
    const pairs = [];
    for (let k = 1; k < n; k++) for (let i = 0; i < n; i++) pairs.push([mod(scale[(i + k) % n] - scale[i], CENTS), k]);
    pairs.sort((x, y) => x[0] - y[0] || x[1] - y[1]);
    const cb = clusterSorted(pairs.map((p) => p[0]), 0.5);
    let violations = 0;
    for (const [s, e] of cb) if (new Set(pairs.slice(s, e).map((p) => p[1])).size > 1) violations++;
    const spec = {};
    for (let k = 1; k < n; k++) spec[k] = Array.from({ length: n }, (_, i) => mod(scale[(i + k) % n] - scale[i], CENTS)).sort((a, b) => a - b);
    let viol = 0, equal = 0;
    for (let k = 1; k < n - 1; k++) {
      const widest = spec[k][n - 1], narrowest = spec[k + 1][0];
      if (widest > narrowest + 1e-9) viol++;
      else if (Math.abs(widest - narrowest) <= 1e-9) equal++;
    }
    const propriety = viol ? "improper" : equal ? "proper" : "strictly_proper";
    return { cs: violations === 0, csViolations: violations, propriety, gapClasses, n };
  }

  // ---------------------------------------------------------------- geometry
  const circ = (a, b) => { const d = Math.abs(mod(a - b, CENTS)); return Math.min(d, CENTS - d); };
  const gapsOf = (cs) => cs.map((a, i) => [a, i < cs.length - 1 ? cs[i + 1] : cs[0] + CENTS]);
  const maxStep = (cs) => Math.max(...gapsOf(cs).map(([a, b]) => b - a));
  function widest(cs) {
    let best = null;
    for (const g of gapsOf(cs)) if (!best || g[1] - g[0] > best[1] - best[0] || (g[1] - g[0] === best[1] - best[0] && g[0] < best[0])) best = g;
    return best;
  }

  // ---------------------------------------------------------------- methods
  function makeCtx(opts) {
    const cap = opts.cap ?? 160, minStep = opts.minStep ?? 20;
    const nSearchMax = opts.nSearchMax ?? 24, budget = opts.budget ?? 200000;
    const inside = (c, lo, hi) => { c = mod(c, CENTS); if (c < lo) c += CENTS; return lo + minStep <= c && c <= hi - minStep; };
    const clearOf = (c, cs) => cs.every((x) => circ(c, x) >= minStep);
    const isCs = (cs) => {
      const n = cs.length, ivs = [];
      for (let k = 1; k < n; k++) for (let i = 0; i < n; i++) ivs.push([mod(cs[(i + k) % n] - cs[i], CENTS), k]);
      ivs.sort((x, y) => x[0] - y[0] || x[1] - y[1]);
      let spans = null, first = null;
      for (const [v, k] of ivs) {
        if (first === null || v - first > 0.5) { spans = new Set(); first = v; }
        spans.add(k);
        if (spans.size > 1) return false;
      }
      return true;
    };
    const need = (cs) => gapsOf(cs).reduce((s, [a, b]) => s + Math.max(0, Math.ceil(Math.trunc(b - a) / Math.trunc(cap)) - 1), 0);

    function csSearch(base, poolIn) {
      const pool = poolIn.map((p) => mod(p, CENTS)).filter((p) => clearOf(p, base)).sort((a, b) => a - b);
      let nodes = 0;
      const sortNum = (xs) => xs.slice().sort((a, b) => a - b);
      function dfs(cs, added, left, start) {
        if (++nodes > budget) throw new Error("budget");
        if (need(cs) > left) return null;
        let cands;
        const filled = maxStep(cs) <= cap;
        if (filled) {
          if (isCs(cs)) return added;
          cands = [];
          for (let i = start; i < pool.length; i++) if (clearOf(pool[i], cs)) cands.push(i);
        } else {
          const [lo, hi] = widest(cs), mid = (lo + hi) / 2;
          cands = pool.map((_, i) => i).filter((i) => inside(pool[i], lo, hi) && clearOf(pool[i], cs))
            .sort((i, j) => Math.abs(mod(pool[i] - lo, CENTS) + lo - mid) - Math.abs(mod(pool[j] - lo, CENTS) + lo - mid) || pool[i] - pool[j]);
        }
        if (left === 0) return null;
        for (const i of cands) {
          const got = dfs(sortNum(cs.concat([pool[i]])), added.concat([pool[i]]), left - 1, filled ? i + 1 : start);
          if (got) return got;
        }
        return null;
      }
      try {
        for (let depth = 0; depth <= nSearchMax - base.length; depth++) {
          const got = dfs(sortNum(base), [], depth, 0);
          if (got) return { added: got.slice().sort((a, b) => a - b), nodes, exhausted: false };
        }
      } catch (e) {
        if (e.message === "budget") return { added: null, nodes, exhausted: true };
        throw e;
      }
      return { added: null, nodes, exhausted: false };
    }

    function greedy(base, pool, keyFn) {
      let cs = base.slice().sort((a, b) => a - b);
      const added = [];
      while (maxStep(cs) > cap) {
        const [lo, hi] = widest(cs), mid = (lo + hi) / 2;
        const cands = pool.filter((it) => inside(it.c, lo, hi) && clearOf(it.c, cs));
        if (!cands.length) return null;
        const k = keyFn || ((it) => [Math.abs(mod(mod(it.c, CENTS) - lo, CENTS) + lo - mid), it.c]);
        let pick = cands[0], pk = k(pick);
        for (const it of cands.slice(1)) {
          const ik = k(it);
          if (ik[0] < pk[0] || (ik[0] === pk[0] && ik[1] < pk[1])) { pick = it; pk = ik; }
        }
        added.push(pick);
        cs = cs.concat([mod(pick.c, CENTS)]).sort((a, b) => a - b);
      }
      return added;
    }

    function splitPoint(a, b, rule) {
      if (rule === "AM") return div(add(a, b), TWO);
      if (rule === "HM") return div(mul(TWO, mul(a, b)), add(a, b));
      return R(a[0] + b[0], a[1] + b[1]);
    }
    function epiFill(tones, rule) {
      let pts = uniqSorted(tones);
      const added = [];
      for (;;) {
        const ext = pts.concat([mul(TWO, pts[0])]);
        let best = null;
        for (let i = 0; i < pts.length; i++) {
          const a = ext[i], b = ext[i + 1], w = centsOf(div(b, a));
          if (w > cap && (!best || w > best.w || (w === best.w && cmp(a, best.a) > 0))) best = { a, b, w };
        }
        if (!best) return added;
        const m = splitPoint(best.a, best.b, rule);
        if (!(centsOf(div(m, best.a)) >= minStep && centsOf(div(best.b, m)) >= minStep)) return null;
        const rm = red(m);
        added.push(rm);
        pts = uniqSorted(pts.concat([rm]));
      }
    }
    return { cap, minStep, csSearch, greedy, epiFill, isCs, clearOf, inside };
  }

  // MERU-001 recurrences and DYNMOS-001 generators (fixed lists).
  const RECURRENCES = [
    ["erv418935", 1, 1, 32, 4], ["erv238186", 1, 1, 2, 3], ["fig12_12", 1, 1, 1, 7], ["erv415227", 4, 8, 8, 9],
    ["metameantone", 2, 3, 2, 4], ["silver414", 8, 9, 7, 10], ["fib", 1, 1, 1, 2], ["metapelog", 1, 1, 1, 3],
    ["metaslendro", 1, 2, 1, 3], ["metaptolemy", 1, 3, 1, 4], ["erv59178", 16, 8, 16, 9], ["llsls", 1, 2, 2, 3],
    ["metaslendro2", 1, 1, 4, 4], ["erv773743", 2, 3, 128, 10], ["pell", 2, 1, 1, 2], ["fit351", 1, 1, 128, 6],
  ];
  const GENERATORS = [
    ["marcus238186", 285.823], ["marcus418935", 502.722], ["gold503786", 503.786], ["gold317170", 317.17],
    ["sub351444", 351.444], ["sub497774", 497.774], ["sub443128", 443.128], ["sub483278", 483.278],
    ["sub175378", 175.378], ["sub316778", 316.778], ["miracle116676", 116.676], ["breed193908", 193.908],
  ];
  function positiveRoot(j, i, a, b) {
    const f = (x) => x ** j - a * x ** (j - i) - b;
    let lo = 1e-9, hi = 1.0;
    while (f(hi) < 0) hi *= 2;
    for (let t = 0; t < 300; t++) { const m = (lo + hi) / 2; if (f(m) < 0) lo = m; else hi = m; }
    return (lo + hi) / 2;
  }
  const pyRound6 = (x) => Math.round(x * 1e6) / 1e6;
  const pyRound = (x) => { const r = Math.round(x); return (Math.abs(x % 1) === 0.5 && r % 2 !== 0) ? r - 1 : r; };
  function recTerms(tones, rec, steps = 130) {
    const [id, a, i, b, j] = rec;
    const log2g = Math.log2(positiveRoot(j, i, a, b));
    const sorted = tones.slice().sort(cmp);
    const align = (base, m) => { const e = pyRound(m * log2g - log2R(base)); return e >= 0 ? mul(base, R(2n ** BigInt(e))) : div(base, R(2n ** BigInt(-e))); };
    const seeds = Array.from({ length: j }, (_, m) => align(sorted[(j <= sorted.length ? m : m % sorted.length)], m));
    const h = seeds.slice();
    const lags = i === j ? [[i, a + b]] : [[i, a], [j, b]];
    for (let n = j; n < j + steps; n++) h.push(lags.reduce((acc, [lag, c]) => add(acc, mul(R(c), h[n - lag])), R(0)));
    const seen = new Set(tones.map(key)), out = [];
    for (const x of h.slice(j)) if (x[0] > 0n) { const r = red(x); if (!seen.has(key(r))) { seen.add(key(r)); out.push(r); } }
    return { id, terms: out, gen01: log2g % 1 };
  }
  function levels(gc) {
    const g = gc / CENTS;
    let lo = [0, 1], hi = [1, 1];
    const out = [];
    for (let t = 0; t < 200; t++) {
      const m = [lo[0] + hi[0], lo[1] + hi[1]];
      if (m[1] > 72) break;
      out.push(m[1]);
      if (g < m[0] / m[1]) hi = m; else lo = m;
    }
    return out.filter((n) => n >= 5);
  }
  // cpsfit001.exact_triads + cpsfit002.prep_triads
  function exactTriads(tones) {
    const shiftOpen = (x, lo, hi) => { let r = x; while (cmp(r, lo) <= 0) r = mul(r, TWO); while (cmp(r, hi) >= 0) r = div(r, TWO); return cmp(lo, r) < 0 && cmp(r, hi) < 0 ? r : null; };
    const idx = new Map(tones.map((t, i) => [key(red(t)), i]));
    const out = [];
    for (const b of tones) {
      const lows = tones.map((pc) => shiftOpen(pc, div(b, TWO), b)).filter(Boolean);
      const highs = tones.map((pc) => shiftOpen(pc, b, mul(TWO, b))).filter(Boolean);
      for (const a of lows) for (const c of highs) {
        if (cmp(div(c, a), TWO) > 0) continue;
        let lab = null;
        if (eq(mul(TWO, b), add(a, c))) lab = "P";
        else if (eq(mul(b, add(a, c)), mul(TWO, mul(a, c)))) lab = "S";
        if (lab) out.push({ lab, mem: [a, b, c].map((x) => [idx.get(key(red(x))), centsOf(x)]), ratios: [a, b, c] });
      }
    }
    return out;
  }
  function triadDevs(tri, pc) {
    return tri.map(({ lab, mem }) => {
      const v = mem.map(([i, cx]) => pc[i] + CENTS * pyRound((cx - pc[i]) / CENTS));
      const [fa, fb, fc] = v.map((x) => 2 ** (x / CENTS));
      const am = (fa + fc) / 2, hm = 2 * fa * fc / (fa + fc);
      const d = lab === "P" ? Math.abs(CENTS * Math.log2(fb / am)) : Math.abs(CENTS * Math.log2(fb / hm));
      return [d, CENTS * Math.log2(am / hm)];
    });
  }
  function bestWindow(tc, tri, gc, n) {
    const ks = Array.from({ length: 2 * n - 1 }, (_, t) => t - (n - 1));
    const ranked = tc.map((t) => {
      const ds = new Map(ks.map((k) => [k, circ(k * gc, t)]));
      return { ds, order: ks.slice().sort((x, y) => ds.get(x) - ds.get(y) || Math.abs(x) - Math.abs(y)) };
    });
    let best = null;
    for (let s = -(n - 1); s <= 0; s++) {
      const lo = s, hi = s + n - 1;
      const assign = ranked.map((r) => r.order.find((k) => lo <= k && k <= hi));
      const errs = assign.map((k, j) => ranked[j].ds.get(k));
      const mx = Math.max(...errs);
      if (mx > 20) continue;
      const pc = assign.map((k) => mod(k * gc, CENTS));
      if (!triadDevs(tri, pc).every(([d, sp]) => d < 2 && sp >= 2)) continue;
      if (!best || mx < best.err || (mx === best.err && -s < best.mode)) best = { mode: -s, assign, err: mx };
    }
    return best;
  }
  function mosWindows(tones) {
    const tc = tones.map(centsOf), tri = exactTriads(tones), out = [];
    for (const [gen, gc] of GENERATORS) {
      for (const n of levels(gc)) {
        const w = bestWindow(tc, tri, gc, n);
        if (!w) continue;
        const ks = Array.from({ length: n }, (_, t) => t - w.mode);
        const used = new Set(w.assign);
        out.push({ gen, gc, N: n, err: w.err, free: ks.filter((k) => !used.has(k)).map((k) => mod(k * gc, CENTS)), chain: ks.map((k) => mod(k * gc, CENTS)).sort((a, b) => a - b) });
        break;
      }
    }
    return out;
  }

  const METHODS = [
    { id: "PARENT-CS", pool: "PARENT", selector: "CS search", tone: "exact" },
    { id: "GENUS-GREEDY", pool: "GENUS", selector: "greedy", tone: "exact" },
    { id: "GENUS-CS", pool: "GENUS", selector: "CS search", tone: "exact" },
    { id: "EPI-AM", pool: "EPI", selector: "constructive", tone: "exact" },
    { id: "EPI-HM", pool: "EPI", selector: "constructive", tone: "exact" },
    { id: "EPI-MED", pool: "EPI", selector: "constructive", tone: "exact" },
    { id: "EPI-CS", pool: "EPI", selector: "CS search", tone: "exact" },
    { id: "REC-GREEDY", pool: "REC", selector: "greedy", tone: "exact (high height)" },
    { id: "REC-CS", pool: "REC", selector: "CS search", tone: "exact (high height)" },
    { id: "MOS-GREEDY", pool: "MOS", selector: "greedy", tone: "tempered" },
    { id: "MOS-CS", pool: "MOS", selector: "CS search", tone: "tempered" },
    { id: "MOS-PURE", pool: "MOS", selector: "retune", tone: "tempered (subset retuned)" },
  ];

  // Every method on one subset. parent / genusTones are rational lists.
  function fillAll(tonesIn, parentTones, genusTones, opts = {}, only = null) {
    const ctx = makeCtx(opts);
    const tones = uniqSorted(tonesIn);
    const tc = tones.map(centsOf);
    const tKeys = new Set(tones.map(key));
    const parentSet = new Set(parentTones.map(key)), genusSet = new Set(genusTones.map(key));
    const res = {};
    const want = (id) => !only || only.includes(id);
    const score = (added, retuned) => {
      const base = retuned || tc;
      const addC = added.map((a) => (Array.isArray(a) ? centsOf(a) : a));
      const cs = base.concat(addC).map((c) => mod(c, CENTS)).sort((a, b) => a - b);
      const tri = triads(cs), tri0 = triads(tc.slice().sort((a, b) => a - b)), m = melodic(cs);
      const exact = added.filter(Array.isArray);
      return {
        n: cs.length, added: added.length, maxStep: maxStep(cs), P: tri.P, S: tri.S, G: tri.G, PS: tri.P + tri.S,
        PSgain: tri.P + tri.S - tri0.P - tri0.S, cs: m.cs, propriety: m.propriety, gapClasses: m.gapClasses,
        exactAdded: exact.length, temperedAdded: added.length - exact.length, retuned: !!retuned,
        maxTenney: exact.length ? Math.max(...exact.map(tenney)) : 0,
        maxPrime: exact.length ? exact.map(maxPrime).reduce((a, b) => (a === null || b === null ? null : Math.max(a, b)), 2) : null,
        inParent: exact.filter((a) => parentSet.has(key(a))).length, inGenus: exact.filter((a) => genusSet.has(key(a))).length,
        addedTones: added, scale: cs,
      };
    };
    const emit = (id, added, retuned, extra = {}) => { res[id] = added ? { ok: true, ...score(added, retuned), ...extra } : { ok: false, ...extra }; };
    const searchExact = (id, pool, extra) => {
      const cents = pool.map((p) => pyRound6(mod(centsOf(p), CENTS)));   // gapfill001 keys the pool at 6 decimals
      const r = ctx.csSearch(tc, cents);
      const back = (c) => pool[cents.indexOf(c)];
      emit(id, r.added && r.added.map(back), null, { nodes: r.nodes, exhausted: r.exhausted, ...extra });
    };
    if (want("PARENT-CS")) {
      const pool = parentTones.filter((p) => !tKeys.has(key(p)));
      if (pool.length) searchExact("PARENT-CS", pool); else emit("PARENT-CS", null, null, { reason: "the subset is the whole structure" });
    }
    const gpool = genusTones.filter((p) => !tKeys.has(key(p)));
    if (want("GENUS-GREEDY")) {
      const g = ctx.greedy(tc, gpool.map((p) => ({ c: centsOf(p), p })), (it) => [tenney(it.p), it.c]);
      emit("GENUS-GREEDY", g && g.map((it) => it.p));
    }
    if (want("GENUS-CS")) searchExact("GENUS-CS", gpool);
    for (const rule of ["AM", "HM", "MED"]) if (want(`EPI-${rule}`)) emit(`EPI-${rule}`, ctx.epiFill(tones, rule));
    if (want("EPI-CS")) {
      const pool = uniqSorted(["AM", "HM", "MED"].flatMap((r) => ctx.epiFill(tones, r) || [])).filter((p) => !tKeys.has(key(p)));
      searchExact("EPI-CS", pool);
    }
    if (want("REC-GREEDY") || want("REC-CS")) {
      let best = null;
      for (const rec of RECURRENCES) {
        const { terms } = recTerms(tones, rec);
        const g = ctx.greedy(tc, terms.map((t, i) => ({ c: centsOf(t), p: t, i })), (it) => [it.i, 0]);
        if (g && (!best || g.length < best.g.length)) best = { rec, g, terms };
      }
      if (best) {
        if (want("REC-GREEDY")) emit("REC-GREEDY", best.g.map((it) => it.p), null, { via: best.rec[0] });
        if (want("REC-CS")) searchExact("REC-CS", best.terms.slice(0, 60), { via: best.rec[0] });
      } else { emit("REC-GREEDY", null); emit("REC-CS", null); }
    }
    if (want("MOS-GREEDY") || want("MOS-CS") || want("MOS-PURE")) {
      const wins = mosWindows(tones);
      let best = null;
      for (const w of wins) {
        const g = ctx.greedy(tc, w.free.map((c) => ({ c })));
        if (g && (!best || g.length < best.g.length || (g.length === best.g.length && w.N < best.w.N))) best = { w, g };
      }
      if (best) {
        if (want("MOS-GREEDY")) emit("MOS-GREEDY", best.g.map((it) => it.c), null, { via: best.w.gen, level: best.w.N });
        if (want("MOS-CS")) { const r = ctx.csSearch(tc, best.w.free); emit("MOS-CS", r.added, null, { via: best.w.gen, level: best.w.N, nodes: r.nodes, exhausted: r.exhausted }); }
      } else { if (want("MOS-GREEDY")) emit("MOS-GREEDY", null); if (want("MOS-CS")) emit("MOS-CS", null); }
      if (want("MOS-PURE")) {
        if (wins.length) {
          const w = wins.reduce((b, x) => (x.N < b.N || (x.N === b.N && x.err < b.err) ? x : b));
          emit("MOS-PURE", [], w.chain, { via: w.gen, level: w.N });
        } else emit("MOS-PURE", null);
      }
    }
    return res;
  }

  root.Engine = {
    R, mul, div, add, cmp, eq, key, str, red, centsOf, tenney, maxPrime, uniqSorted,
    cps, genus, subCps, censusSubsets, triads, melodic, exactTriads, maxStep, fillAll, recTerms,
    METHODS, RECURRENCES, GENERATORS,
  };
  if (typeof module !== "undefined") module.exports = root.Engine;
})(typeof window !== "undefined" ? window : globalThis);
