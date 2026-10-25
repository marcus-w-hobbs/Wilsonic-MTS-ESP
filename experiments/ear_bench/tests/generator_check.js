// Cross-checks docs/ear-bench/generator.js against registered results, so the
// generator explorer stays faithful to what the experiments measured.
// Run by test_generator.py; exits 1 on the first mismatch.
"use strict";

const path = require("path");
const G = require(path.join(__dirname, "..", "..", "..", "docs", "ear-bench", "generator.js"));

const failures = [];
const expect = (label, got, want) => {
  if (JSON.stringify(got) !== JSON.stringify(want)) failures.push(`${label}: got ${JSON.stringify(got)}, want ${JSON.stringify(want)}`);
};
const heldAt2 = (structure, cents, n) => {
  const p = G.place(cents / 1200, n, structure);
  return G.triads(structure, p).filter((t) => t.present && Math.abs(t.dev) <= 2).length;
};

const hexany = G.cps([1, 3, 5, 7], 2);
const dekany = G.cps([1, 3, 5, 7, 9], 2);
const eikosany = G.cps([1, 3, 5, 7, 9, 11], 3);
expect("hexany size and exact triads", [hexany.tones.length, hexany.triads.length], [6, 12]);
expect("dekany size and exact triads", [dekany.tones.length, dekany.triads.length], [10, 41]);
expect("eikosany size and exact triads", [eikosany.tones.length, eikosany.triads.length], [20, 114]);

// Registered triad survival at 2c (CPSFIT-001/002/003, DYNMOS-001).
expect("CPSFIT-001 N22 193.7867", heldAt2(hexany, 193.7867, 22), 10);
expect("CPSFIT-001 N15 502.8604", heldAt2(hexany, 502.8604, 15), 2);
expect("CPSFIT-002 N16 116.5878", heldAt2(hexany, 116.5878, 16), 6);
expect("CPSFIT-002 N22 193.9083", heldAt2(hexany, 193.9083, 22), 12);
expect("CPSFIT-003 N16 116.6755", heldAt2(hexany, 116.6755, 16), 10);
expect("CPSFIT-003 N18 77.8177", heldAt2(hexany, 77.8177, 18), 10);
expect("CPSFIT-003 dekany N26 498.066", heldAt2(dekany, 498.066, 26), 32);
expect("DYNMOS-001 hexany[in=5,out=7] 351.444 N17", heldAt2(G.cps([1, 3, 9, 11], 2), 351.444, 17), 8);

// SUBFIT-002 hexanies kept (every exact triad of the hexany within 2c).
const hexaniesKept = (cents, n) => {
  const p = G.place(cents / 1200, n, eikosany);
  const tri = G.triads(eikosany, p);
  let kept = 0;
  for (let fin = 0; fin < 6; fin++) for (let fout = 0; fout < 6; fout++) {
    if (fin === fout) continue;
    const set = eikosany.tones.map((t, i) => [t, i]).filter(([t]) => t.factors.includes(fin) && !t.factors.includes(fout)).map(([, i]) => i);
    const ts = tri.filter((t) => t.tones.every((i) => set.includes(i)));
    if (ts.length && ts.every((t) => t.present && Math.abs(t.dev) <= 2)) kept += 1;
  }
  return kept;
};
expect("SUBFIT-002 351.444 N41 hexanies", hexaniesKept(351.444, 41), 14);
expect("SUBFIT-002 443.128 N46 hexanies", hexaniesKept(443.128, 46), 12);
expect("SUBFIT-002 497.774 N53 hexanies", hexaniesKept(497.774, 53), 16);
expect("SUBFIT-002 483.278 N72 hexanies", hexaniesKept(483.278, 72), 20);

// Single val is prime-based (9 costs twice 3). Recorded 2026-10-24: the
// 41-note level of 351.444c places the eikosany on the val (3, 5, 7, 11) ->
// (2, 25, 13, 5) generators, which SUBFIT-002's post-hoc solve did not find.
expect("single val 351.444 N41", G.singleVal(eikosany, G.place(351.444 / 1200, 41, eikosany)), true);
expect("single val 497.774 N53", G.singleVal(eikosany, G.place(497.774 / 1200, 53, eikosany)), true);

// MOS levels of the golden noble nearest Erv's 0.418935.
expect("MOS levels of 0.418836", G.mosLevels(0.418836, 120).map((l) => l.n), [2, 3, 5, 7, 12, 19, 31, 43, 74, 117]);

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log("generator.js reproduces every registered check");
