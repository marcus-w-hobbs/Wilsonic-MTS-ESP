// Checks this page's engine against the GAPFILL-001 receipts: every method on all
// 126 subsets, compared row by row (added tones, size, triads, CS, propriety).
// Run from the repo root:  node docs/crossroads/check_engine.js [METHOD,METHOD,...]
// All 1,512 rows matched on 2026-10-27 (receipts v1.0.1); a full run takes about 2 minutes.
"use strict";
const E = require("./engine.js");
const fs = require("fs");
const rows = fs.readFileSync(require("path").join(__dirname, "../../experiments/lattice/results/gapfill001.jsonl"), "utf8").trim().split("\n").map(JSON.parse);
const idx = new Map(rows.map(r => [`${r.seedset}|${r.subset}|${r.method}`, r]));
const SEEDS = { canonical: [1,3,5,7,9,11], flagship: [1,7,9,11,15,29], marcus: [1,45,135,225,19,377] };
const only = process.argv[2] ? process.argv[2].split(",") : null;
const tally = {}; const bad = [];
const t0 = Date.now();
for (const [set, seeds] of Object.entries(SEEDS)) {
  const parent = E.cps(seeds, 3), gen = E.genus(seeds);
  for (const sub of E.censusSubsets(seeds)) {
    const res = E.fillAll(sub.tones, parent, gen, {}, only);
    for (const [m, r] of Object.entries(res)) {
      const py = idx.get(`${set}|${sub.name}|${m}`);
      if (!py) { bad.push([set, sub.name, m, "no python row"]); continue; }
      const t = tally[m] ||= { rows: 0, match: 0 };
      t.rows++;
      const diffs = [];
      if (py.ok !== r.ok) diffs.push(`ok ${py.ok}/${r.ok}`);
      else if (py.ok) {
        const pyAdd = py.added_tones.map(String).sort().join(" ");
        const jsAdd = r.addedTones.map(a => Array.isArray(a) ? E.str(a) : String(Math.round(a * 1e4) / 1e4)).sort().join(" ");
        if (pyAdd !== jsAdd) diffs.push(`added [${pyAdd}] vs [${jsAdd}]`);
        for (const [pk, jk] of [["n","n"],["P","P"],["S","S"],["cs","cs"],["propriety","propriety"],["gap_classes","gapClasses"]]) if (py[pk] !== r[jk]) diffs.push(`${pk} ${py[pk]}/${r[jk]}`);
        if (Math.abs(py.max_step - r.maxStep) > 1e-3) diffs.push(`max_step ${py.max_step}/${r.maxStep}`);
      }
      if (diffs.length) bad.push([set, sub.name, m, diffs.join("; ")]); else t.match++;
    }
  }
}
console.log(JSON.stringify(tally));
console.log("mismatching rows:", bad.length, "time", ((Date.now()-t0)/1000).toFixed(1)+"s");
for (const b of bad.slice(0, 25)) console.log(" ", b.join(" | ").slice(0, 300));
