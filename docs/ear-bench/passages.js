// Listening passages: each passage plays in both chains as X then Y, in an
// order hidden from the listener and drawn fresh for every page load. A pick
// (X, Y or Same) is saved with the hidden mapping and resolved to A or B, and
// only then is the mapping shown.
"use strict";

const Passages = (() => {
  const LIST = [
    ["run", "Scale run", "Melody alone: the scale up and down one octave."],
    ["tune", "Tune", "Melody alone: a line in the scale's own steps, walking from chord tone to chord tone."],
    ["chorale", "Chorale", "Harmony alone: every triad of the reference, held, moving by common tones, with a bass."],
    ["over", "Tune over chorale", "Melody and harmony together: the tune above a softer chorale."],
  ];
  const PAUSE = 1.2;
  let blind = {};
  let blindFor = "";

  function shuffle(pairKey) {
    if (blindFor === pairKey) return;
    blindFor = pairKey;
    blind = Object.fromEntries(LIST.map(([id]) => [id, Math.random() < 0.5 ? "a" : "b"]));
  }

  function schedule(events, t0, hz) {
    events.forEach((e) => Synth.blip(hz(e.cents), t0 + e.t, e.dur, e.level));
    return t0 + Composer.length(events);
  }

  function render(box, ctx) {
    const { a, b, ref, pairKey } = ctx;
    shuffle(pairKey);
    const music = Composer.compose(a, b, ref);
    const saved = (ctx.saved() || {}).picks || {};
    const other = (s) => (s === "a" ? "b" : "a");
    const name = (slot) => (slot === "a" ? "A" : "B");

    box.innerHTML = `
      <p class="hint">Each passage plays twice, once in each scale, as <strong>X</strong> then <strong>Y</strong>. Which is A and which is B is hidden until you pick, and drawn fresh each time the page loads.
      The ${music.chords} chords come from <span class="mono">${ctx.escape(ref.name)}</span>, so both scales play the same music.</p>
      <div class="p-list">
        ${LIST.map(([id, title, desc]) => {
          const pick = saved[`passage:${id}`];
          const x = pick ? pick.x : blind[id];
          const verdict = pick
            ? `<span class="p-result">You chose ${pick.pick === "same" ? "Same" : pick.pick.toUpperCase()}: ${pick.preferred === "same" ? "no preference" : `prefer ${name(pick.preferred)}`}. X was ${name(x)}, Y was ${name(other(x))}.</span>`
            : "";
          return `
          <div class="p-row">
            <div class="p-text"><strong>${title}</strong><span class="hint">${desc} ${Math.round(Composer.length(music.a[id]))} s each.</span></div>
            <div class="seg">
              <button class="btn sm" data-pplay="xy" data-id="${id}">Play X then Y</button>
              <button class="btn sm" data-pplay="x" data-id="${id}">X</button>
              <button class="btn sm" data-pplay="y" data-id="${id}">Y</button>
            </div>
            <div class="seg">
              <span class="label">Prefer</span>
              ${[["x", "X"], ["y", "Y"], ["same", "Same"]].map(([v, l]) => `<button class="btn sm ${pick && pick.pick === v ? "on" : ""}" data-ppick="${v}" data-id="${id}" ${ctx.readOnly ? "disabled" : ""}>${l}</button>`).join("")}
            </div>
            ${verdict}
          </div>`;
        }).join("")}
      </div>
      <div class="row"><button class="btn sm" id="p-stop">Stop</button><span class="hint">Esc also stops.</span></div>`;

    const slotOf = (id, which) => {
      const pick = saved[`passage:${id}`];
      const x = pick ? pick.x : blind[id];
      return which === "x" ? x : other(x);
    };
    box.querySelectorAll("[data-pplay]").forEach((btn) => btn.addEventListener("click", async () => {
      await ctx.ensureAudio();
      Synth.allOff();
      const id = btn.dataset.id;
      const t0 = Synth.now() + 0.1;
      const mode = btn.dataset.pplay;
      if (mode === "xy") {
        const end = schedule(music[slotOf(id, "x")][id], t0, ctx.hz);
        schedule(music[slotOf(id, "y")][id], end + PAUSE, ctx.hz);
      } else {
        schedule(music[slotOf(id, mode)][id], t0, ctx.hz);
      }
    }));
    box.querySelectorAll("[data-ppick]").forEach((btn) => btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      const pickV = btn.dataset.ppick;
      const x = slotOf(id, "x");
      const preferred = pickV === "same" ? "same" : pickV === "x" ? x : other(x);
      const cur = ctx.saved() || {};
      ctx.save({ prefer: cur.prefer || null, picks: { ...(cur.picks || {}), [`passage:${id}`]: { x, pick: pickV, preferred, at: new Date().toISOString() } } });
      render(box, ctx);
    }));
    box.querySelector("#p-stop").addEventListener("click", () => Synth.allOff());
  }

  return { render, LIST };
})();
