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
  const CHORDAL = new Set(["tune", "chorale", "over"]);
  let blind = {};
  let blindFor = "";
  // What is sounding now: {id, title, segs: [{label, t0, t1}], chordNames, notes}.
  // Only X/Y labels are ever shown, never which scale they are.
  let playing = null;
  let raf = 0;

  const clock = (sec) => `${Math.floor(sec / 60)}:${String(Math.floor(sec % 60)).padStart(2, "0")}`;

  function where(p, seg, into) {
    if (CHORDAL.has(p.id) && p.chordNames.length) {
      const i = Math.min(p.chordNames.length - 1, Math.floor(into / Composer.SLOT));
      const c = p.chordNames[i];
      return `chord ${i + 1} of ${p.chordNames.length} · ${c.form || "?"} (${c.kind === "P" ? "proportional" : "subcontrary"})`;
    }
    const n = Math.min(p.notes, Math.floor(into / Composer.STEP) + 1);
    return `note ${n} of ${p.notes} · ${n <= Math.ceil(p.notes / 2) ? "going up" : "coming down"}`;
  }

  function paintNow() {
    const el = document.getElementById("p-now");
    if (!el) { raf = 0; return; }
    document.querySelectorAll(".p-row").forEach((r) => r.classList.toggle("playing", !!playing && !playing.done && r.dataset.row === playing.id));
    if (!playing) {
      el.innerHTML = `<span class="hint">Nothing playing. Press <strong>Play X then Y</strong> on a passage.</span>`;
      raf = 0;
      return;
    }
    const t = Synth.now();
    const total = playing.segs[playing.segs.length - 1].t1 - playing.segs[0].t0;
    const active = playing.segs.find((sg) => t >= sg.t0 && t < sg.t1);
    const next = playing.segs.find((sg) => t < sg.t0);
    const finished = t >= playing.segs[playing.segs.length - 1].t1;
    const lane = (label) => {
      const sg = playing.segs.find((x) => x.label === label);
      if (!sg) return `<div class="p-lane off"><span class="p-letter">${label}</span><span class="hint">not in this play</span></div>`;
      const frac = Math.max(0, Math.min(1, (t - sg.t0) / (sg.t1 - sg.t0)));
      const state = t < sg.t0 ? "waiting" : t < sg.t1 ? "sounding" : "done";
      return `<div class="p-lane ${state}"><span class="p-letter">${label}</span>
        <span class="p-bar"><span style="width:${(frac * 100).toFixed(1)}%"></span></span>
        <span class="mono p-time">${state === "sounding" ? `${clock(t - sg.t0)} / ${clock(sg.t1 - sg.t0)}` : state}</span></div>`;
    };
    const status = finished
      ? `<strong>Finished: ${playing.title}.</strong> Pick X, Y or Same.`
      : active
        ? `<strong>${active.label} is sounding</strong> · ${playing.title} · ${where(playing, active, t - active.t0)}`
        : `<strong>Pause</strong> · ${next ? `${next.label} next` : ""}`;
    el.innerHTML = `<div class="p-lanes">${lane("X")}${lane("Y")}</div>
      <div class="p-status">${status} <span class="hint mono">${clock(Math.min(total, Math.max(0, t - playing.segs[0].t0)))} / ${clock(total)}</span></div>`;
    if (finished) { playing = { ...playing, done: true }; raf = 0; return; }
    raf = requestAnimationFrame(paintNow);
  }

  function startNow(p) {
    playing = p;
    if (!raf) raf = requestAnimationFrame(paintNow);
  }

  function stopNow() {
    playing = null;
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
    paintNow();
  }

  // One hidden X/Y draw per passage per timbre, so judging the same passage
  // under another timbre is a fresh blind trial.
  function shuffle(pairKey) {
    if (blindFor === pairKey) return;
    blindFor = pairKey;
    blind = {};
  }
  function blindOf(id) {
    const k = `${id}@${Synth.timbre}`;
    if (!blind[k]) blind = { ...blind, [k]: Math.random() < 0.5 ? "a" : "b" };
    return blind[k];
  }

  // Picks are kept per timbre: "passage:<id>@<timbre>". Older picks saved as
  // "passage:<id>" count for the timbre they were made under (reed before
  // listening context was recorded).
  const pickKey = (id, timbre = Synth.timbre) => `passage:${id}@${timbre}`;
  const legacyTimbre = (pick) => (pick && pick.context && pick.context.timbre) || "reed";
  function pickFor(saved, id, timbre = Synth.timbre) {
    const legacy = saved[`passage:${id}`];
    return saved[pickKey(id, timbre)] || (legacy && legacyTimbre(legacy) === timbre ? legacy : null);
  }
  function otherTimbrePicks(saved, id) {
    return Object.entries(saved)
      .filter(([k, v]) => v && typeof v === "object" && (k.startsWith(`passage:${id}@`) || k === `passage:${id}`))
      .map(([k, v]) => ({ timbre: k.includes("@") ? k.split("@")[1] : legacyTimbre(v), pick: v }))
      .filter((x) => x.timbre !== Synth.timbre);
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
      Picks are kept separately for each timbre; you are judging under <strong>${ctx.escape((Timbres.ALL[Synth.timbre] || {}).label || Synth.timbre)}</strong>.
      The ${music.chords} chords come from <span class="mono">${ctx.escape(ref.name)}</span>, so both scales play the same music.</p>
      <div class="p-now" id="p-now" role="status"></div>
      <div class="p-list">
        ${LIST.map(([id, title, desc]) => {
          const pick = pickFor(saved, id);
          const x = pick ? pick.x : blindOf(id);
          const others = otherTimbrePicks(saved, id).map((o) => `${(Timbres.ALL[o.timbre] || {}).label ? Timbres.ALL[o.timbre].label.split(" (")[0] : o.timbre}: ${o.pick.preferred === "same" ? "same" : `prefer ${name(o.pick.preferred)}`}`);
          const verdict = pick
            ? `<span class="p-result">You chose ${pick.pick === "same" ? "Same" : pick.pick.toUpperCase()}: ${pick.preferred === "same" ? "no preference" : `prefer ${name(pick.preferred)}`}. X was ${name(x)}, Y was ${name(other(x))}.</span>`
            : "";
          return `
          <div class="p-row" data-row="${id}">
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
            ${others.length ? `<span class="p-others hint">Other timbres: ${others.join(" · ")}</span>` : ""}
          </div>`;
        }).join("")}
      </div>
      <div class="row"><button class="btn sm" id="p-stop">Stop</button><span class="hint">Esc also stops.</span></div>`;

    const slotOf = (id, which) => {
      const pick = pickFor(saved, id);
      const x = pick ? pick.x : blindOf(id);
      return which === "x" ? x : other(x);
    };
    box.querySelectorAll("[data-pplay]").forEach((btn) => btn.addEventListener("click", async () => {
      await ctx.ensureAudio();
      Synth.allOff();
      const id = btn.dataset.id;
      const t0 = Synth.now() + 0.1;
      const mode = btn.dataset.pplay;
      const title = LIST.find(([k]) => k === id)[1];
      const base = { id, title, chordNames: music.chordNames, notes: music.a[id].length };
      if (mode === "xy") {
        const end = schedule(music[slotOf(id, "x")][id], t0, ctx.hz);
        const end2 = schedule(music[slotOf(id, "y")][id], end + PAUSE, ctx.hz);
        startNow({ ...base, segs: [{ label: "X", t0, t1: end }, { label: "Y", t0: end + PAUSE, t1: end2 }] });
      } else {
        const end = schedule(music[slotOf(id, mode)][id], t0, ctx.hz);
        startNow({ ...base, segs: [{ label: mode.toUpperCase(), t0, t1: end }] });
      }
    }));
    box.querySelectorAll("[data-ppick]").forEach((btn) => btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      const pickV = btn.dataset.ppick;
      const x = slotOf(id, "x");
      const preferred = pickV === "same" ? "same" : pickV === "x" ? x : other(x);
      const cur = ctx.saved() || {};
      ctx.save({ prefer: cur.prefer || null, picks: { ...(cur.picks || {}), [pickKey(id)]: { x, pick: pickV, preferred, at: new Date().toISOString(), context: ctx.context() } } });
      render(box, ctx);
    }));
    box.querySelector("#p-stop").addEventListener("click", () => { Synth.allOff(); stopNow(); });
    paintNow();
    if (playing && !playing.done && !raf) raf = requestAnimationFrame(paintNow);
  }

  return { render, LIST, stopNow };
})();
