// Compare A and B: when both slots hold chains of the same JI reference, list
// the reference's chords side by side, ordered by how much the two chains
// differ, with play buttons and a per-chord pick that saves with the verdicts.
"use strict";

const Compare = (() => {
  const HOLD = 4;

  const keyOf = (t, off) => `${t.kind}:${t.ji.map((c) => (c - off).toFixed(1)).join(",")}`;

  function rows(a, b, ref) {
    const A = Targets.compute(a, ref);
    const B = Targets.compute(b, ref);
    const bByKey = new Map(B.triads.map((t) => [keyOf(t, B.align.off), t]));
    return A.triads
      .map((ta) => ({ key: keyOf(ta, A.align.off), a: ta, b: bByKey.get(keyOf(ta, A.align.off)) }))
      .filter((r) => r.b)
      .sort((x, y) => Math.abs(Math.abs(y.a.dev) - Math.abs(y.b.dev)) - Math.abs(Math.abs(x.a.dev) - Math.abs(x.b.dev)));
  }

  function render(box, ctx) {
    const { a, b } = ctx;
    const ref = a && b && a.reference && a.reference === b.reference ? ctx.scaleOf(a.reference) : null;
    if (!ref) { box.hidden = true; return; }
    box.hidden = false;
    const list = rows(a, b, ref);
    const saved = ctx.saved() || {};
    const picks = saved.picks || {};
    const tol = ctx.tol();
    const devCell = (t) => `<span class="mono t-dev ${Math.abs(t.dev) <= tol ? "ok" : "bad"}">${ctx.fmt(t.dev)}¢</span>`;
    const pickBtns = (key) => [["a", "A"], ["b", "B"], ["same", "Same"]].map(([v, l]) =>
      `<button class="btn sm ${picks[key] === v ? "on" : ""}" data-pick="${v}" data-key="${ctx.escape(key)}" ${ctx.readOnly ? "disabled" : ""}>${l}</button>`).join("");
    const inA = list.filter((r) => Math.abs(r.a.dev) <= tol).length;
    const inB = list.filter((r) => Math.abs(r.b.dev) <= tol).length;
    const wasOpen = !!(box.querySelector(".c-detail") && box.querySelector(".c-detail").open);
    box.innerHTML = `
      <div class="c-head"><h3>Listening passages</h3></div>
      <div id="passages"></div>
      <details class="c-detail" ${wasOpen ? "open" : ""}>
      <summary><strong>Chord by chord</strong> <span class="hint">(not blind: A and B are named)</span></summary>
      <p class="hint">Each row is one chord of <span class="mono">${ctx.escape(ref.name)}</span>, played in both chains. The rows where A and B differ most come first.
        A keeps ${inA} of ${list.length} within ${tol.toFixed(2)}¢, B keeps ${inB}. Chords hold ${HOLD} s so slow beats have time to show.</p>
      <div class="c-table" role="table" aria-label="Chords in A and B">
        <div class="c-row c-th" role="row"><span>Chord</span><span>A</span><span>B</span><span>Play</span><span>Which locks better?</span></div>
        ${list.map((r, i) => `
        <div class="c-row" role="row">
          <span><span class="kchip k-${r.a.kind}">${r.a.kind}</span> <strong class="mono">${r.a.form || "?"}</strong></span>
          ${devCell(r.a)}
          ${devCell(r.b)}
          <span class="seg">
            <button class="btn sm" data-play="a" data-i="${i}">A</button>
            <button class="btn sm" data-play="b" data-i="${i}">B</button>
            <button class="btn sm" data-play="ab" data-i="${i}">A then B</button>
            <button class="btn sm" data-play="ji" data-i="${i}">JI</button>
          </span>
          <span class="seg">${pickBtns(r.key)}</span>
        </div>`).join("")}
      </div>
      <div class="row c-melody">
        <span class="label">Melody</span>
        <button class="btn sm" id="c-run">Scale run, A then B</button>
        <button class="btn sm" id="c-phrase" ${ctx.hasPhrase() ? "" : "disabled"}>Your recorded phrase, A then B</button>
        <span class="sep"></span>
        <span class="label">Overall</span>
        ${[["a", "A"], ["b", "B"], ["same", "Same to me"]].map(([v, l]) => `<button class="btn sm ${saved.prefer === v ? "on" : ""}" data-overall="${v}" ${ctx.readOnly ? "disabled" : ""}>${l}</button>`).join("")}
      </div>
      </details>`;

    Passages.render(box.querySelector("#passages"), { ...ctx, ref, pairKey: `${a.id}|${b.id}` });
    const chord = (slot, r) => (slot === "a" ? r.a : r.b);
    box.querySelectorAll("[data-play]").forEach((btn) => btn.addEventListener("click", async () => {
      await ctx.ensureAudio();
      const r = list[Number(btn.dataset.i)];
      const mode = btn.dataset.play;
      if (mode === "ab") ctx.playTriad(r.b, ctx.playTriad(r.a, undefined, HOLD), HOLD);
      else if (mode === "ji") ctx.playTriad({ cents: r.a.ji }, undefined, HOLD);
      else ctx.playTriad(chord(mode, r), undefined, HOLD);
    }));
    box.querySelectorAll("[data-pick]").forEach((btn) => btn.addEventListener("click", () => {
      const cur = ctx.saved() || {};
      const key = btn.dataset.key;
      const next = { ...(cur.picks || {}), [key]: cur.picks && cur.picks[key] === btn.dataset.pick ? null : btn.dataset.pick };
      ctx.save({ prefer: cur.prefer || null, picks: next });
      render(box, ctx);
    }));
    box.querySelectorAll("[data-overall]").forEach((btn) => btn.addEventListener("click", () => {
      const cur = ctx.saved() || {};
      ctx.save({ prefer: cur.prefer === btn.dataset.overall ? null : btn.dataset.overall, picks: cur.picks || {} });
      render(box, ctx);
    }));
    box.querySelector("#c-run").addEventListener("click", async () => { await ctx.ensureAudio(); ctx.runAThenB(); });
    box.querySelector("#c-phrase").addEventListener("click", async () => { await ctx.ensureAudio(); ctx.phraseAThenB(); });
  }

  return { render };
})();
