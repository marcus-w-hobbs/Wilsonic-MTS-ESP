// Checks docs/ear-bench/compose.js on the bundled scales: the chorale is the
// same in both scales of a gap fill (they keep the reference's tones exactly),
// and the added-harmony passage plays only each chain's own triads that the
// reference lacks, capped, in a fixed order. Run by test_compose.py.
"use strict";

const fs = require("fs");
const path = require("path");
const BENCH = path.join(__dirname, "..", "..", "..", "docs", "ear-bench");
global.Tuning = require(path.join(BENCH, "tuning.js"));
global.Targets = require(path.join(BENCH, "targets.js"));
const Composer = require(path.join(BENCH, "compose.js"));

const data = JSON.parse(fs.readFileSync(path.join(BENCH, "data.json"), "utf8"));
const byId = new Map(data.scales.map((s) => [s.id, s]));
const failures = [];
const expect = (label, got, want) => {
  if (JSON.stringify(got) !== JSON.stringify(want)) failures.push(`${label}: got ${JSON.stringify(got)}, want ${JSON.stringify(want)}`);
};
const scale = (id) => {
  const s = byId.get(id);
  if (!s) throw new Error(`missing scale ${id}`);
  return s;
};
const pitches = (events) => events.map((e) => e.cents.toFixed(3)).join(" ");
const chordsOf = (events) => events.filter((e) => e.tag.role === "chord");

const G = "lattice.gapfill001.canonical_";
const am = scale(`${G}hexany_in9_out11_EPI-AM`);
const parent = scale(`${G}hexany_in9_out11_PARENT-CS`);
const ref = scale(am.reference);
const music = Composer.compose(am, parent, ref);
expect("gap fills share the reference's 12 chords", music.chords, 12);
expect("gap-fill chorales are identical", pitches(music.a.chorale), pitches(music.b.chorale));
expect("EPI-AM adds 14 chords at 2c", music.a.addedTotal, 14);
expect("PARENT-CS adds 18 chords at 2c", music.b.addedTotal, 18);
expect("PARENT-CS plays the cap", music.b.addedNames.length, Composer.MAX_ADDED);
expect("added passage: three chord tones and a bass per chord", music.a.added.length, 4 * music.a.addedNames.length);
expect("same music on a second compose", pitches(Composer.compose(am, parent, ref).a.added), pitches(music.a.added));

// Every added chord is the chain's own triad within 2c, and none is the reference's.
const chain = Tuning.model(am);
const { align, triads } = Targets.compute(am, ref);
const pcSet = (cents) => cents.map((c) => (((Math.round(c * 1000) / 1000) % 1200) + 1200) % 1200).sort((x, y) => x - y).join(",");
const refSets = new Set(triads.map((t) => `${t.kind}:${pcSet(t.cents)}`));
const added = Composer.addedTriads(chain, triads);
expect("added triads all within 2c", added.triads.every((t) => Math.abs(t.dev) <= 2), true);
expect("no added triad is a reference triad", added.triads.filter((t) => refSets.has(`${t.kind}:${pcSet(t.cents)}`)).length, 0);
expect("reference aligned exactly (scl cents carry 6 decimals)", align.worst < 1e-3, true);

// A dense tempered chain is capped; its chorale differs from a just fill's.
const pure = scale(`${G}hexany_in9_out11_MOS-PURE`);
const tempered = Composer.compose(am, pure, ref);
expect("MOS-PURE adds 134 chords, plays 16", [tempered.b.addedTotal, tempered.b.addedNames.length], [134, Composer.MAX_ADDED]);
expect("tempered chorale differs", pitches(tempered.a.chorale) === pitches(tempered.b.chorale), false);

// The dekany fills now have their subset as the reference.
const dek = scale(`${G}dekany_in_in1_outnone_EPI-AM`);
expect("dekany fill reference", dek.reference, "lattice.subsetmel000.sm000_1-3-5-7-9-11_dekany_in_in1_outnone_cs");
const dmusic = Composer.compose(dek, scale(`${G}dekany_in_in1_outnone_PARENT-CS`), scale(dek.reference));
expect("dekany chorale identical", pitches(dmusic.a.chorale), pitches(dmusic.b.chorale));
expect("dekany chorale non-empty", chordsOf(dmusic.a.chorale).length > 0, true);

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log(`compose_check: ok (dekany chorale ${dmusic.chords} chords; dekany adds ${dmusic.a.addedTotal} / ${dmusic.b.addedTotal})`);
