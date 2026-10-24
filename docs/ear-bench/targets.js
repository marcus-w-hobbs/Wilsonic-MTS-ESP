// Target triads: the JI reference's own triads (the hexany's twelve, the
// dekany's 41, the eikosany's 114), placed in the chain on its nearest tones.
// This is the count the fit experiments register, so each row is something
// the gate is actually asking about. Each row can play JI then chain.
"use strict";

const Targets = (() => {
  const cache = new Map();

  function compute(chainScale, refScale) {
    const key = `${chainScale.id}|${refScale.id}`;
    if (!cache.has(key)) {
      const chain = Tuning.model(chainScale);
      const ref = Tuning.model(refScale);
      const align = Tuning.alignReference(chain, ref);
      cache.set(key, { align, triads: Tuning.targetTriads(chain, ref, align) });
    }
    return cache.get(key);
  }

  function render(box, s, ref, ctx) {
    const { align, triads } = compute(s, ref);
    const shown = triads.filter((t) => ctx.kinds().includes(t.kind));
    const inside = triads.filter((t) => Math.abs(t.dev) <= ctx.tol()).length;
    const worst = triads.reduce((m, t) => Math.max(m, Math.abs(t.dev)), 0);
    box.innerHTML = `
      <div class="t-head">
        <h3>Target triads in ${ctx.escape(ctx.label(s))}</h3>
        ${ctx.viewToggle()}
        <p class="hint"><strong>${inside} of ${triads.length}</strong> triads of <span class="mono">${ctx.escape(ref.name)}</span> within ${ctx.tol().toFixed(2)}¢ · worst ${worst.toFixed(2)}¢ · reference tones land within ${align.worst.toFixed(2)}¢ in this alignment</p>
      </div>
      ${ctx.controls()}
      <div class="t-list" role="list">
        ${shown.map((t, i) => {
          const ok = Math.abs(t.dev) <= ctx.tol();
          return `
          <div class="t-row target ${ok ? "" : "miss"}" role="listitem" data-tri="${i}">
            <span class="kchip k-${t.kind}">${t.kind}</span>
            <button class="t-play" data-tt="${i}" aria-label="Play ${t.form || "triad"} in the chain"><span class="t-form">${t.form || "?"}</span> <span class="mono">${t.degrees.join("·")}</span></button>
            <span class="mono t-dev ${ok ? "ok" : "bad"}">${ctx.fmt(t.dev)}¢</span>
            <button class="btn sm" data-ji="${i}" aria-label="Play ${t.form || "triad"} in JI, then in the chain">JI → chain</button>
          </div>`;
        }).join("")}
      </div>`;
    ctx.bindControls(box);
    const n = Tuning.model(s).n;
    const mark = (t) => ctx.markStrip({ kind: t.kind, idx: new Set(t.degrees.map((d) => ((d % n) + n) % n)) });
    box.querySelectorAll("[data-tt]").forEach((b) => {
      const t = shown[Number(b.dataset.tt)];
      b.addEventListener("mouseenter", () => mark(t));
      b.addEventListener("focus", () => mark(t));
      b.addEventListener("mouseleave", () => ctx.markStrip());
      b.addEventListener("click", async () => { await ctx.ensureAudio(); ctx.playTriad(t); });
    });
    box.querySelectorAll("[data-ji]").forEach((b) => {
      const t = shown[Number(b.dataset.ji)];
      b.addEventListener("click", async () => {
        await ctx.ensureAudio();
        const next = ctx.playTriad({ cents: t.ji });
        ctx.playTriad(t, next);
      });
    });
  }

  return { render, compute };
})();
