// Ear Bench passages: the same music composed in two chains, so a listener
// judges melody, harmony and both together without playing anything.
//   run     the chain's scale, one period up and down
//   chorale every triad of the JI reference, held, each chord moving to the
//           next by common tones, with a bass an octave below the root
//   tune    a melody in the chain's own steps that walks from chord tone to
//           chord tone, one chord's time per target
//   over    the tune above a softer chorale
//   added   the chain's own triads that the reference does not have (the
//           harmony a gap fill grows), held, by common tones, with a bass
// The progression is fixed by the reference (identical in both chains); the
// pitches are each chain's nearest tones. The added chords are each chain's
// own, so X and Y play different chords there. Pure functions: events only.
"use strict";

const Composer = (() => {
  const CHORD = 2.2;
  const GAP = 0.15;
  const STEP = 0.22;
  const SLOT = CHORD + GAP;
  const CENTER = 700;
  // Added harmony: the page's triad finder at the triad scorer's 2c, capped so
  // a dense chain still plays in well under a minute (closest chords first).
  const ADDED_TOL = 2;
  const MAX_ADDED = 16;

  const pc = (c) => ((Math.round(c * 10) / 10) % 1200 + 1200) % 1200;
  const sameTone = (x, y) => Math.min(Math.abs(x - y), 1200 - Math.abs(x - y)) < 1;
  const keyOf = (t, off) => `${t.kind}:${t.ji.map((c) => (c - off).toFixed(1)).join(",")}`;

  // Order the reference triads: start on the lowest proportional triad, then
  // always move to an unvisited triad sharing the most tones (ties: least motion).
  function progression(triads, off) {
    const items = triads.map((t) => ({ key: keyOf(t, off), pcs: t.ji.map((c) => pc(c - off)), center: (t.ji[0] + t.ji[2]) / 2 - off }));
    const shared = (x, y) => x.pcs.filter((p) => y.pcs.some((q) => sameTone(p, q))).length;
    const start = [...items].sort((x, y) => (x.key[0] === "P" ? 0 : 1) - (y.key[0] === "P" ? 0 : 1) || x.center - y.center)[0];
    const order = [start];
    let left = items.filter((x) => x !== start);
    while (left.length) {
      const prev = order[order.length - 1];
      const next = [...left].sort((x, y) => shared(y, prev) - shared(x, prev) || Math.abs(pc(x.center) - pc(prev.center)) - Math.abs(pc(y.center) - pc(prev.center)))[0];
      order.push(next);
      left = left.filter((x) => x !== next);
    }
    return order.map((x) => x.key);
  }

  // Octave shift per chord (from the reference, so both chains get the same
  // register): keeps each chord's middle near CENTER cents above 1/1.
  function shifts(order, byKey, off) {
    return order.map((k) => {
      const t = byKey.get(k);
      const mid = t.ji[1] - off;
      return 1200 * Math.round((CENTER - mid) / 1200);
    });
  }

  // A triad's shape on the chain: root degree class, then the other two
  // degrees above it, so a reference triad and the same chord found in the
  // chain compare equal wherever their octaves sit.
  const shapeOf = (t, n) => `${t.kind}:${((t.degrees[0] % n) + n) % n}:${t.degrees[1] - t.degrees[0]}:${t.degrees[2] - t.degrees[0]}`;

  // The chain's own triads that are not the reference's (in chain order: the
  // finder lists the closest first), at most MAX_ADDED of them.
  function addedTriads(chain, targets) {
    const have = new Set(targets.map((t) => shapeOf(t, chain.n)));
    const found = Tuning.findTriads(chain, ADDED_TOL).filter((t) => !have.has(shapeOf(t, chain.n)));
    return { total: found.length, triads: found.slice(0, MAX_ADDED) };
  }

  // The added chords as a chorale of their own: common-tone order, each
  // chord's middle near CENTER cents above the chain's 1/1.
  function addedChords(triads) {
    const items = triads.map((t) => ({ ...t, ji: t.cents }));
    const by = new Map(items.map((t) => [keyOf(t, 0), t]));
    const order = progression(items, 0);
    const shift = shifts(order, by, 0);
    return {
      chords: order.map((k, i) => ({ cents: by.get(k).cents, shift: shift[i] })),
      names: order.map((k) => ({ kind: by.get(k).kind, form: by.get(k).form })),
    };
  }

  function chorale(chords, level = 1) {
    return chords.flatMap(({ cents, shift }, i) => [
      ...cents.map((c, v) => ({ t: i * SLOT, dur: CHORD, cents: c + shift, level, tag: { role: "chord", i, v } })),
      { t: i * SLOT, dur: CHORD, cents: cents[0] + shift - 1200, level: level * 0.8, tag: { role: "bass", i, v: 0 } },
    ]);
  }

  // Melody: walk the chain's degrees toward each chord's top tone, an octave up.
  function tune(chain, chords) {
    const slots = Math.floor(SLOT / STEP);
    const events = [];
    let cur = Tuning.nearestDegree(chain, chords[0].cents[0] + chords[0].shift + 1200);
    chords.forEach(({ cents, shift }, i) => {
      const target = Tuning.nearestDegree(chain, cents[2] + shift + 1200);
      const dist = target - cur;
      let path;
      if (Math.abs(dist) < 2) {
        path = [target + 1, target - 1, target];
      } else {
        const stride = Math.max(1, Math.ceil(Math.abs(dist) / (slots - 1)));
        path = [];
        for (let d = cur + Math.sign(dist) * stride; Math.sign(target - d) === Math.sign(dist); d += Math.sign(dist) * stride) path.push(d);
        path.push(target);
      }
      path.forEach((d, j) => {
        const last = j === path.length - 1;
        events.push({ t: i * SLOT + j * STEP, dur: last ? SLOT - j * STEP - 0.05 : STEP * 0.95, cents: Tuning.degreeCents(chain, d), level: 1, tag: { role: "tune", i, v: 0 } });
      });
      cur = target;
    });
    return events;
  }

  function run(chain) {
    const up = Array.from({ length: chain.n + 1 }, (_, d) => Tuning.degreeCents(chain, d));
    return [...up, ...up.slice(0, -1).reverse()].map((c, i) => ({ t: i * STEP, dur: STEP * 0.95, cents: c, level: 1, tag: { role: "run", i, v: 0 } }));
  }

  // Both chains' passages from one reference progression.
  // anchor: play the structure at its own pitch (its 1/1 on the bench's 1/1)
  // whatever chain carries it, so switching generator or level changes only
  // the tuning and never transposes the music. Chord notes are already in A's
  // frame; run and tune notes are in their own chain's frame.
  function compose(a, b, ref, { anchor = false } = {}) {
    const A = Targets.compute(a, ref);
    const B = Targets.compute(b, ref);
    const aBy = new Map(A.triads.map((t) => [keyOf(t, A.align.off), t]));
    const bBy = new Map(B.triads.map((t) => [keyOf(t, B.align.off), t]));
    const order = progression(A.triads, A.align.off).filter((k) => bBy.has(k));
    const shiftA = shifts(order, aBy, A.align.off);
    const forChain = (scale, by, align) => {
      const chain = Tuning.model(scale);
      // Same register in both chains: shift by the reference, measured from each chain's own alignment.
      const chords = order.map((k, i) => ({ cents: by.get(k).cents, shift: shiftA[i] - align.off + A.align.off }));
      const extra = addedTriads(chain, [...by.values()]);
      const grown = addedChords(extra.triads);
      const place = (events) => (anchor
        ? events.map((e) => ({ ...e, cents: e.cents - (e.tag.role === "chord" || e.tag.role === "bass" ? A.align.off : align.off) }))
        : events);
      return {
        run: place(run(chain)),
        chorale: place(chorale(chords)),
        tune: place(tune(chain, chords)),
        over: place([...chorale(chords, 0.55), ...tune(chain, chords)]),
        // Added chords are the chain's own, so anchoring removes its own offset.
        added: anchor ? chorale(grown.chords).map((e) => ({ ...e, cents: e.cents - align.off })) : chorale(grown.chords),
        addedNames: grown.names,
        addedTotal: extra.total,
      };
    };
    // Chord identities in playing order (same for both chains, so naming them stays blind).
    const chordNames = order.map((k) => {
      const t = aBy.get(k);
      return { kind: t.kind, form: t.form };
    });
    return { chords: order.length, chordNames, a: forChain(a, aBy, A.align), b: forChain(b, bBy, B.align) };
  }

  const length = (events) => events.reduce((m, e) => Math.max(m, e.t + e.dur), 0);

  return { compose, length, progression, addedTriads, SLOT, STEP, MAX_ADDED };
})();

if (typeof module !== "undefined") module.exports = Composer;
