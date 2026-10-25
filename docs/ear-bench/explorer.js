// Generator explorer: choose a generator up front (as a fraction of the
// octave, e.g. 0.418, or in cents, e.g. 502.7c), choose any combination
// product set, and see how the CPS sits on the nearest golden nobles' MOS
// levels. Click a level to hear it; set two levels as A and B for the blind
// passages. The math is generator.js; the palette is palette.json.
"use strict";

const Explorer = (() => {
  const NEIGHBOURS = 8;
  const MAX_N = 120;
  const PRESETS = [
    { id: "hex1357", label: "Hexany 1·3·5·7", seeds: [1, 3, 5, 7], k: 2 },
    { id: "dek13579", label: "Dekany 1·3·5·7·9", seeds: [1, 3, 5, 7, 9], k: 2 },
    { id: "eik", label: "Eikosany 1·3·5·7·9·11", seeds: [1, 3, 5, 7, 9, 11], k: 3 },
    { id: "eikM", label: "Eikosany 1·45·135·225·19·377", seeds: [1, 45, 135, 225, 19, 377], k: 3 },
  ];
  const KEY = "earbench.explorer.v1";

  let palette = null;
  let input = { gen: "0.418", preset: "eik", seeds: "1, 3, 5, 7, 9, 11", k: 3, band: 1 };
  let selected = null; // {row, n}, or {row, nearN} while a switch is resolving
  const cache = new Map();
  // What the explorer is playing now: {pid, t0, end, scaleId}. While it plays,
  // clicking a level, typing a generator or choosing a structure moves the
  // sounding and remaining notes there at once (live retargeting).
  let live = null;
  const isLive = () => !!live && Synth.now() < live.end;

  try { input = { ...input, ...JSON.parse(localStorage.getItem(KEY) || "{}") }; } catch (e) { /* storage blocked */ }
  const remember = () => { try { localStorage.setItem(KEY, JSON.stringify(input)); } catch (e) { /* ignore */ } };

  async function loadPalette() {
    if (palette) return palette;
    const res = await fetch("palette.json");
    if (!res.ok) throw new Error(`palette.json: HTTP ${res.status}`);
    palette = await res.json();
    return palette;
  }

  // "0.418" -> 0.418; "502.7c" or "502.7 cents" -> 502.7/1200; folded into (0, 0.5].
  function parseGenerator(text) {
    const t = String(text).trim().toLowerCase();
    const cents = /c(ents)?$/.test(t);
    const v = parseFloat(t);
    if (!Number.isFinite(v) || v <= 0) return null;
    let g = cents ? v / 1200 : v > 1 ? v / 1200 : v;
    g = g % 1;
    if (g > 0.5) g = 1 - g;
    return g > 0 ? g : null;
  }

  function structureSpec() {
    const preset = PRESETS.find((p) => p.id === input.preset);
    if (preset) return { seeds: preset.seeds, k: preset.k, label: preset.label };
    const seeds = String(input.seeds).split(/[\s,·]+/).map(Number).filter((x) => Number.isFinite(x) && x > 0);
    const k = Math.max(1, Math.min(seeds.length - 1, Math.round(Number(input.k)) || 1));
    return { seeds, k, label: `CPS(${seeds.length},${k}) ${seeds.join("·")}` };
  }

  const structKey = (spec) => `cps.${spec.k}.${spec.seeds.join("-")}`;

  function compute(g, spec) {
    const key = `${g.toFixed(9)}|${structKey(spec)}`;
    if (!cache.has(key)) {
      const nearest = [...palette.nobles].sort((x, y) => Math.abs(x.g - g) - Math.abs(y.g - g)).slice(0, NEIGHBOURS).sort((x, y) => x.g - y.g);
      const structure = Generator.cps(spec.seeds, spec.k);
      const rows = nearest.map((noble) => ({ noble, levels: Generator.profile(noble.g, structure, { maxN: MAX_N }) }));
      cache.set(key, { structure, rows });
    }
    return cache.get(key);
  }

  // Register the structure and a chosen level as bench scales, so the
  // passages, triad card and judgments treat them like any other scale.
  function registerLevel(ctx, spec, structure, noble, level) {
    const refId = structKey(spec);
    if (!ctx.scaleOf(refId)) {
      ctx.register({ id: refId, name: spec.label, cents: [...structure.tones.slice(1).map((t) => t.cents), 1200], explorer: true });
    }
    const id = `gen.${noble.g.toFixed(9)}.${level.n}.${refId}`;
    if (!ctx.scaleOf(id)) {
      ctx.register({
        id, name: `${noble.g.toFixed(6)} · ${level.n} notes`, description: `golden noble ${noble.seeds} (complexity ${noble.complexity}), ${level.n}-note MOS level, ${spec.label}`,
        cents: Generator.chainScale(noble.g, level.placement), reference: refId, explorer: true,
        stimulus: {
          family: "golden", generator: noble.g, generatorCents: noble.cents, seeds: noble.seeds, complexity: noble.complexity,
          notes: level.n, window: level.placement.window, cps: { seeds: spec.seeds, k: spec.k },
          heldAt: { 2: level.held[0], 5: level.held[1], 10: level.held[2] }, triads: level.totalTriads,
          tones: level.tones, worstTone: level.worstTone, worstTriad: level.worstTriad, singleVal: level.singleVal,
          steps: { large: level.large, small: level.small },
        },
      });
    }
    return id;
  }

  function cellColour(frac) {
    // Fraction of triads held in the chosen band, on the accent ramp.
    return `color-mix(in srgb, var(--accent) ${Math.round(frac * 85)}%, var(--paper))`;
  }

  function render(box, ctx) {
    box.innerHTML = `<p class="hint">Loading the golden palette…</p>`;
    loadPalette().then(() => paint(box, ctx)).catch((err) => { box.innerHTML = `<p class="warn">${ctx.escape(err.message)}</p>`; });
  }

  function paint(box, ctx) {
    const g = parseGenerator(input.gen);
    const spec = structureSpec();
    const bands = Generator.BANDS;
    const band = Math.min(bands.length - 1, Math.max(0, input.band));
    const ok = g && spec.seeds.length >= 2 && spec.k >= 1 && spec.k < spec.seeds.length;
    const data = ok ? compute(g, spec) : null;
    if (data && selected && selected.nearN) {
      const row = Math.min(selected.row, data.rows.length - 1);
      const levels = data.rows[row].levels;
      const near = levels.length ? levels.reduce((b, l) => (Math.abs(l.n - selected.nearN) < Math.abs(b.n - selected.nearN) ? l : b)) : null;
      selected = near ? { row, n: near.n } : null;
    }

    box.innerHTML = `
      <div class="x-controls">
        <label class="ctl" for="x-gen">Generator <input id="x-gen" type="text" value="${ctx.escape(input.gen)}" placeholder="0.418 or 502.7c" size="10"></label>
        <label class="ctl" for="x-preset">Structure
          <select id="x-preset">${PRESETS.map((p) => `<option value="${p.id}" ${p.id === input.preset ? "selected" : ""}>${p.label}</option>`).join("")}
            <option value="custom" ${input.preset === "custom" ? "selected" : ""}>Custom CPS…</option></select></label>
        ${input.preset === "custom" ? `
          <label class="ctl" for="x-seeds">Seeds <input id="x-seeds" type="text" value="${ctx.escape(input.seeds)}" size="18"></label>
          <label class="ctl" for="x-k">k <input id="x-k" type="number" min="1" max="8" value="${input.k}" style="width:56px"></label>` : ""}
        <div class="ctl"><span>Count triads within</span><div class="seg">${bands.map((b, i) => `<button class="btn sm ${i === band ? "on" : ""}" data-band="${i}">${b}¢</button>`).join("")}</div></div>
      </div>
      <p class="hint">${ok ? `The ${NEIGHBOURS} golden nobles nearest ${g.toFixed(6)} (${(g * 1200).toFixed(3)}¢), each at its MOS levels from ${data.structure.tones.length} to ${MAX_N} notes. Each cell shows how many of the ${data.structure.triads.length} exact triads of ${ctx.escape(spec.label)} the level holds within ${bands[band]}¢; a ring marks each row's smallest level holding its best count. 2¢ is the registered tier; 5¢ and 10¢ are listening bands from G-029, provisional until EAR-ε. Nearby nobles can differ sharply at high levels: nobility says nothing about harmony.` : "Type a generator as a fraction of the octave (0.418) or in cents (502.7c), and a CPS with at least two seeds."}</p>
      ${ok ? `<div class="x-grid" role="grid">${data.rows.map((row, ri) => {
        const best = Math.max(0, ...row.levels.map((l) => l.held[band]));
        const floor = row.levels.find((l) => l.held[band] === best && best > 0);
        return `<div class="x-row" role="row">
          <div class="x-head" role="rowheader"><span class="mono">${row.noble.g.toFixed(6)}</span><span class="hint mono">${row.noble.cents.toFixed(3)}¢ · c${row.noble.complexity}</span></div>
          <div class="x-cells">${row.levels.map((l) => {
            const isSel = selected && selected.row === ri && selected.n === l.n;
            const frac = l.totalTriads ? l.held[band] / l.totalTriads : 0;
            const tip = `${l.n} notes · tones ${l.tones}/${l.totalTones} within 20¢ · triads within 2/5/10¢: ${l.held.join("/")} of ${l.totalTriads} · worst triad ${l.worstTriad === null ? "–" : l.worstTriad.toFixed(2) + "¢"} · worst tone ${l.worstTone === null ? "–" : l.worstTone.toFixed(2) + "¢"} · steps ${l.large.toFixed(1)}/${l.small.toFixed(1)}¢ · ${l.singleVal ? "single val" : l.singleVal === false ? "not a single val" : ""}`;
            return `<button class="x-cell ${isSel ? "sel" : ""} ${floor && floor.n === l.n ? "floor" : ""}" role="gridcell" data-row="${ri}" data-n="${l.n}" title="${tip}" style="background:${cellColour(frac)}">
              <span class="x-n">${l.n}</span><span class="x-held mono">${l.held[band]}/${l.totalTriads}</span>${l.singleVal ? `<span class="x-val" aria-label="single val">•</span>` : ""}</button>`;
          }).join("") || `<span class="hint">no MOS level between ${data.structure.tones.length} and ${MAX_N} notes</span>`}</div></div>`;
      }).join("")}</div>
      <div class="x-detail" id="x-detail"></div>` : ""}`;

    const rerender = () => { remember(); paint(box, ctx); };
    // While something plays, a new generator or structure keeps the selection
    // on the same row and the nearest level, so the music moves there.
    const carry = () => (isLive() && selected && selected.n ? { row: selected.row, nearN: selected.n } : null);
    const gen = box.querySelector("#x-gen");
    gen.addEventListener("change", () => { input = { ...input, gen: gen.value }; selected = carry(); rerender(); });
    box.querySelector("#x-preset").addEventListener("change", (e) => { input = { ...input, preset: e.target.value }; selected = carry(); rerender(); });
    const seeds = box.querySelector("#x-seeds");
    if (seeds) seeds.addEventListener("change", () => { input = { ...input, seeds: seeds.value }; selected = carry(); rerender(); });
    const k = box.querySelector("#x-k");
    if (k) k.addEventListener("change", () => { input = { ...input, k: Number(k.value) }; selected = carry(); rerender(); });
    box.querySelectorAll("[data-band]").forEach((b) => b.addEventListener("click", () => { input = { ...input, band: Number(b.dataset.band) }; rerender(); }));
    box.querySelectorAll(".x-cell").forEach((c) => c.addEventListener("click", () => {
      selected = { row: Number(c.dataset.row), n: Number(c.dataset.n) };
      paint(box, ctx);
    }));
    if (data && selected) detail(box.querySelector("#x-detail"), ctx, spec, data, bands);
  }

  function detail(el, ctx, spec, data, bands) {
    const row = data.rows[selected.row];
    const level = row && row.levels.find((l) => l.n === selected.n);
    if (!level) { el.innerHTML = ""; return; }
    const id = registerLevel(ctx, spec, data.structure, row.noble, level);
    const scale = ctx.scaleOf(id);
    const ref = ctx.scaleOf(scale.reference);
    const music = Composer.compose(scale, scale, ref, { anchor: true });
    const saved = ctx.savedScale(id) || {};
    if (isLive() && live.scaleId !== id) retarget(ctx, id);
    el.innerHTML = `
      ${isLive() ? `<p class="x-live"><strong>Live:</strong> ${ctx.escape(Passages.LIST.find(([k]) => k === live.pid)[1])} is playing here. Click another level, type a generator or choose a structure and the sounding notes jump there at once.</p>` : ""}
      <div class="x-sum">
        <h4 class="mono">${row.noble.g.toFixed(6)} · ${level.n} notes</h4>
        <span class="hint">golden noble ${ctx.escape(row.noble.seeds)}, complexity ${row.noble.complexity} · steps ${level.large.toFixed(2)} and ${level.small.toFixed(2)}¢ (ratio ${level.ratio.toFixed(2)}) · tones ${level.tones} of ${level.totalTones} within 20¢ (worst ${level.worstTone === null ? "–" : level.worstTone.toFixed(2)}¢) · triads within ${bands.join("/")}¢: ${level.held.join("/")} of ${level.totalTriads} (worst ${level.worstTriad === null ? "–" : level.worstTriad.toFixed(2)}¢) · ${level.singleVal ? "single val" : level.singleVal === false ? "not a single val" : "val not checked"}</span>
      </div>
      <div class="row">
        <span class="label">Hear it</span>
        ${Passages.LIST.map(([pid, title]) => `<button class="btn sm" data-xplay="${pid}">${title}</button>`).join("")}
        <button class="btn sm" id="x-stop">Stop</button>
        <span class="sep"></span>
        <button class="btn sm ${ctx.isA(id) ? "on" : ""}" id="x-a">Set as A</button>
        <button class="btn sm ${ctx.isB(id) ? "on" : ""}" id="x-b">Set as B</button>
      </div>
      <div class="row">
        <span class="label">Does it work musically?</span>
        ${[1, 2, 3, 4, 5].map((n) => `<button class="dot ${saved.rating === n ? "on" : ""}" data-xrate="${n}" aria-label="Rate ${n} of 5">${n}</button>`).join("")}
        <input type="text" id="x-note" placeholder="Note on this level" value="${ctx.escape(saved.note || "")}" style="flex:1 1 220px">
      </div>`;
    el.querySelectorAll("[data-xplay]").forEach((b) => b.addEventListener("click", async () => {
      await ctx.ensureAudio();
      Synth.allOff();
      const t0 = Synth.now() + 0.1;
      const events = music.a[b.dataset.xplay];
      events.forEach((e) => Synth.blip(ctx.hz(e.cents), t0 + e.t, e.dur, e.level, { ...e.tag, cents: e.cents }));
      live = { pid: b.dataset.xplay, t0, end: t0 + Composer.length(events) + 0.5, scaleId: id };
      detail(el, ctx, spec, data, bands);
    }));
    el.querySelector("#x-stop").addEventListener("click", () => { Synth.allOff(); live = null; detail(el, ctx, spec, data, bands); });
    el.querySelector("#x-a").addEventListener("click", () => { ctx.setA(id); detail(el, ctx, spec, data, bands); });
    el.querySelector("#x-b").addEventListener("click", () => { ctx.setB(id); detail(el, ctx, spec, data, bands); });
    el.querySelectorAll("[data-xrate]").forEach((b) => b.addEventListener("click", () => {
      const cur = ctx.savedScale(id) || {};
      const n = Number(b.dataset.xrate);
      ctx.saveScale(id, { gate: null, rating: cur.rating === n ? null : n, note: el.querySelector("#x-note").value, stimulus: scale.stimulus, context: ctx.context() });
      detail(el, ctx, spec, data, bands);
    }));
    el.querySelector("#x-note").addEventListener("change", (e) => {
      const cur = ctx.savedScale(id) || {};
      ctx.saveScale(id, { gate: null, rating: cur.rating || null, note: e.target.value, stimulus: scale.stimulus, context: ctx.context() });
    });
  }

  // Move what is playing onto another level (another generator, number of
  // notes or structure). A sounding note becomes the note with the same role
  // (chord voice, bass, tune or run) sounding at this moment in the new
  // music, or else the nearest tone of the new scale; notes not yet started
  // are dropped and the new music is scheduled from this moment on.
  function retarget(ctx, toId) {
    const scale = ctx.scaleOf(toId);
    const ref = scale && ctx.scaleOf(scale.reference);
    if (!scale || !ref) return;
    const events = Composer.compose(scale, scale, ref, { anchor: true }).a[live.pid];
    const now = Synth.now();
    const elapsed = now - live.t0;
    const sounding = events.filter((e) => e.t <= elapsed && elapsed < e.t + e.dur);
    const model = Tuning.model(scale);
    Synth.retuneSounding((note) => {
      const same = sounding.find((e) => e.tag.role === note.tag.role && e.tag.v === note.tag.v);
      const cents = same ? same.cents : Tuning.degreeCents(model, Tuning.nearestDegree(model, note.tag.cents));
      return ctx.hz(cents);
    });
    Synth.cancelPending();
    events.filter((e) => e.t > elapsed).forEach((e) => Synth.blip(ctx.hz(e.cents), live.t0 + e.t, e.dur, e.level, { ...e.tag, cents: e.cents }));
    live = { ...live, scaleId: toId, end: live.t0 + Composer.length(events) + 0.5 };
  }

  return { render, parseGenerator };
})();
