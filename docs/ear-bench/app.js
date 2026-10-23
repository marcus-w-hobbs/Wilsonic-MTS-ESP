// Ear Bench UI: gate queue, instrument (pitch strip, computer keys, MIDI,
// A/B with phrase replay), triad list, and verdict capture.
"use strict";

(() => {
  const $ = (sel, root = document) => root.querySelector(sel);
  const escape = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const KEY_ROWS = [
    ["KeyZ", "KeyX", "KeyC", "KeyV", "KeyB", "KeyN", "KeyM", "Comma", "Period", "Slash"],
    ["KeyA", "KeyS", "KeyD", "KeyF", "KeyG", "KeyH", "KeyJ", "KeyK", "KeyL", "Semicolon", "Quote"],
    ["KeyQ", "KeyW", "KeyE", "KeyR", "KeyT", "KeyY", "KeyU", "KeyI", "KeyO", "KeyP", "BracketLeft", "BracketRight"],
    ["Digit1", "Digit2", "Digit3", "Digit4", "Digit5", "Digit6", "Digit7", "Digit8", "Digit9", "Digit0", "Minus", "Equal"],
  ];
  const KEY_INDEX = new Map(KEY_ROWS.flat().map((code, i) => [code, i]));
  const HOME_INDEX = KEY_INDEX.get("KeyA");
  const TRIAD_ROW_LIMIT = 120;

  const state = {
    data: null, byId: new Map(), groupId: null,
    a: null, b: null, slot: "a",
    tol: 2, kinds: "PS", triadView: "target", offset: -HOME_INDEX, stripOct: 0, baseHz: 261.6256,
    blindNames: false, shuffle: null, drone: false,
    recording: false, phrase: [], t0: 0, held: new Map(), sustain: false, sustained: new Set(),
    epsDraft: { verdict: null, fusion: null, notes: "" }, spaceHold: null,
  };

  // ---------- helpers ----------
  const hz = (cents) => state.baseHz * Math.pow(2, cents / 1200);
  const scaleOf = (id) => state.byId.get(id);
  const active = () => scaleOf(state.slot === "b" && state.b ? state.b : state.a);
  const fmt = (x, d = 2) => (x >= 0 ? "+" : "−") + Math.abs(x).toFixed(d);
  const shortGate = (g) => g.gate.split(/[:;]/)[0].replace(/ review$/, "");
  const groups = () => {
    const out = [];
    const { gates, scales } = state.data;
    gates.forEach((g) => out.push({ id: g.id, kind: "gate", gate: g, title: shortGate(g), scales: scales.filter((s) => s.gate === g.id) }));
    const folders = [...new Set(scales.filter((s) => !s.gate).map((s) => `${s.module}/${s.folder}`))];
    folders.forEach((f) => out.push({ id: `lib-${f.replace(/[^a-z0-9]+/gi, "-")}`, kind: "library", title: f === "triads/triads" ? "Triad archive (JI)" : f, scales: scales.filter((s) => !s.gate && `${s.module}/${s.folder}` === f) }));
    return out;
  };
  const currentGroup = () => groups().find((g) => g.id === state.groupId);
  const label = (s) => {
    if (!state.blindNames || !state.shuffle) return s.name;
    return `Scale ${state.shuffle.get(s.id)}`;
  };

  async function ensureAudio() {
    const ok = await Synth.start();
    const btn = $("#audio");
    btn.textContent = ok ? "Audio on" : "Start audio";
    btn.classList.toggle("on", ok);
    return ok;
  }

  // ---------- playing ----------
  function play(key, cents) {
    if (!Synth.running()) return;
    Synth.noteOn(key, hz(cents));
    state.held.set(key, cents);
    if (state.recording) state.phrase.push({ t: Synth.now() - state.t0, key, cents, on: true });
    markStrip();
  }
  function release(key) {
    if (state.sustain && key.startsWith("midi")) { state.sustained.add(key); return; }
    Synth.noteOff(key);
    state.held.delete(key);
    if (state.recording) state.phrase.push({ t: Synth.now() - state.t0, key, on: false });
    markStrip();
  }
  function stopAll() {
    Synth.allOff();
    state.held.clear();
    state.sustained.clear();
    state.drone = false;
    renderInstrumentBar();
    markStrip();
  }
  function playDegree(key, d) {
    const s = active();
    if (s) play(key, Tuning.degreeCents(Tuning.model(s), d));
  }

  function sequence(centsList, step = 0.3, hold = 0.28) {
    const t = Synth.now() + 0.05;
    centsList.forEach((c, i) => Synth.blip(hz(c), t + i * step, hold));
  }
  function runScale(s = active(), t0 = Synth.now() + 0.05) {
    const m = Tuning.model(s);
    const up = Array.from({ length: m.n + 1 }, (_, d) => Tuning.degreeCents(m, d));
    const notes = [...up, ...up.slice(0, -1).reverse()];
    notes.forEach((c, i) => Synth.blip(hz(c), t0 + i * 0.3, 0.28));
    return t0 + notes.length * 0.3 + 0.8;
  }
  function playTriad(tr, t = Synth.now() + 0.05, hold = 1.5) {
    tr.cents.forEach((c, i) => Synth.blip(hz(c), t + i * 0.22, 0.2));
    tr.cents.forEach((c) => Synth.blip(hz(c), t + 0.75, hold));
    return t + 0.75 + hold + 0.35;
  }
  function runAThenB() { runScale(scaleOf(state.b), runScale(scaleOf(state.a))); }
  function phraseAThenB() { replayOn(state.b, replayOn(state.a)); }
  function playAllTriads() {
    let t = Synth.now() + 0.05;
    visibleTriads().slice(0, 24).forEach((tr) => { t = playTriad(tr, t); });
  }
  function toggleDrone() {
    state.drone = !state.drone;
    if (state.drone) Synth.noteOn("drone", hz(-1200));
    else Synth.noteOff("drone");
    renderInstrumentBar();
  }

  function phraseNotes() {
    const notes = [];
    const open = new Map();
    state.phrase.forEach((ev) => {
      if (ev.on) open.set(ev.key, ev);
      else if (open.has(ev.key)) { const on = open.get(ev.key); notes.push({ start: on.t, dur: ev.t - on.t, cents: on.cents }); open.delete(ev.key); }
    });
    open.forEach((on) => notes.push({ start: on.t, dur: 0.4, cents: on.cents }));
    return notes;
  }
  function replayOn(id, t = Synth.now() + 0.05) {
    const s = scaleOf(id);
    if (!s) return t;
    const m = Tuning.model(s);
    const notes = phraseNotes();
    notes.forEach((n) => Synth.blip(hz(Tuning.degreeCents(m, Tuning.nearestDegree(m, n.cents))), t + n.start, Math.max(0.08, n.dur)));
    return t + notes.reduce((e, n) => Math.max(e, n.start + n.dur), 0) + 0.8;
  }

  // ---------- triads ----------
  let triadCache = { key: "", list: [] };
  function triadsFor(s) {
    const key = `${s.id}|${state.tol}`;
    if (triadCache.key !== key) triadCache = { key, list: Tuning.findTriads(Tuning.model(s), state.tol) };
    return triadCache.list;
  }
  const visibleTriads = () => triadsFor(active()).filter((t) => state.kinds.includes(t.kind));

  // ---------- rendering: sidebar ----------
  function renderSidebar() {
    const gs = groups();
    const verdictChip = (g) => {
      if (g.kind !== "gate") return "";
      if (g.gate.protocol === "eareps" || g.id === "G-025") {
        const r = (Store.get("eareps", "responses") || {}).responses || {};
        const n = Object.values(r).filter((x) => x.verdict).length;
        return n ? `<span class="chip">${n}/44</span>` : "";
      }
      const v = Store.get("gates", g.id);
      return v && v.verdict ? `<span class="chip v-${v.verdict}">${v.verdict === "again" ? "again" : v.verdict}</span>` : "";
    };
    const item = (g) => `
      <a class="q-item ${g.id === state.groupId ? "on" : ""}" href="#${g.id}" data-group="${g.id}">
        <span class="q-id">${g.kind === "gate" ? g.id : "Library"}</span>
        <span class="q-title">${escape(g.title)}</span>
        <span class="q-meta">${g.scales.length} scale${g.scales.length === 1 ? "" : "s"} ${verdictChip(g)}</span>
      </a>`;
    const pending = gs.filter((g) => g.kind === "gate" && g.gate.state === "PENDING");
    const decided = gs.filter((g) => g.kind === "gate" && g.gate.state !== "PENDING");
    const library = gs.filter((g) => g.kind === "library");
    $("#queue").innerHTML = `
      <p class="eyebrow">Waiting on your ear · ${pending.length}</p>${pending.map(item).join("")}
      <p class="eyebrow">Decided, still playable</p>${decided.map(item).join("")}
      <p class="eyebrow">Library</p>${library.map(item).join("")}`;
  }

  // ---------- rendering: main ----------
  function selectGroup(id) {
    const gs = groups();
    const g = gs.find((x) => x.id === id) || gs[0];
    state.groupId = g.id;
    state.shuffle = null;
    state.blindNames = false;
    state.spaceHold = null;
    const playable = g.scales.filter((s) => s.protocol !== "eareps");
    const pair = g.gate && g.gate.pair && g.gate.pair.every((id) => state.byId.has(id)) ? g.gate.pair : null;
    state.a = pair ? pair[0] : playable[0] ? playable[0].id : null;
    state.b = pair ? pair[1] : playable[1] ? playable[1].id : null;
    state.slot = "a";
    renderSidebar();
    renderMain();
    window.scrollTo(0, 0);
  }

  function renderMain() {
    const g = currentGroup();
    const isEps = g.scales.some((s) => s.protocol === "eareps");
    $("#main").innerHTML = `
      <header class="g-head">
        <p class="eyebrow">${g.kind === "gate" ? `${g.id} · opened ${g.gate.opened} · ${g.gate.state}` : "Library · no gate"}</p>
        <h2>${escape(g.title)}</h2>
        ${g.kind === "gate" ? `<p class="gate-text">${escape(g.gate.gate)}</p><p class="ledger">${escape(g.gate.status)}</p>` : ""}
      </header>
      ${isEps ? "" : `<section class="card compare" id="compare" hidden></section>`}
      ${g.kind === "gate" && !isEps ? `<section class="card verdict" id="verdict"></section>` : ""}
      ${isEps ? `<div id="eps"></div>` : `
      <details class="explore" id="explore" ${g.kind === "gate" ? "" : "open"}>
        <summary>
          <h3>Explore on your own</h3>
          <span class="hint">${g.kind === "gate" ? "Optional. The two cards above are all a verdict needs." : "Play, compare and inspect the scales in this folder."}</span>
        </summary>
        <ul class="explore-key">
          <li><strong>Instrument:</strong> play either scale yourself (computer keys, MIDI, or click the bars), record a phrase and replay it on A or B.</li>
          <li><strong>Scales:</strong> every scale in this gate's folder. Choose which is A and B, and rate or note any of them.</li>
          <li><strong>Triads:</strong> one scale at a time, either the reference's own triads in it (Target) or every triad it contains (All).</li>
          <li><strong>Tuning:</strong> the numbers: cents, ratios, steps and Hz.</li>
        </ul>
        <section class="card instrument" id="instrument">
          <div id="inst-bar"></div>
          <div class="strip-wrap" id="strip-wrap"></div>
          <div id="inst-actions"></div>
        </section>
        <div class="cols">
          <section class="card" id="scales"></section>
          <section class="card" id="triads"></section>
        </div>
        <section class="card" id="table"></section>
      </details>`}`;
    if (isEps) renderEps();
    else {
      if (g.kind === "gate") renderVerdict(true);
      renderInstrument();
      renderScales();
    }
  }

  function renderEps() {
    const g = currentGroup();
    Eareps.render($("#eps"), g.scales, {
      escape, hz, ensureAudio, baseHz: () => state.baseHz,
      get draft() { return state.epsDraft; },
      set draft(d) { state.epsDraft = d; },
      setDraft: (d, rerender = true) => { state.epsDraft = d; if (rerender) renderEps(); },
      setSpaceHold: (on, off) => { state.spaceHold = { on, off }; },
    });
  }

  // ----- verdict card -----
  let notesTimer = null;
  function renderVerdict(full) {
    const g = currentGroup();
    const box = $("#verdict");
    if (!box || g.kind !== "gate") return;
    const v = Store.get("gates", g.id) || {};
    const choices = [["pass", "Pass"], ["fail", "Fail"], ["again", "Listen again"]];
    const label = { pass: "Pass", fail: "Fail", again: "Listen again" }[v.verdict] || "none yet";
    const status = v.updatedAt ? `Saved ${new Date(v.updatedAt).toLocaleString()} · verdict: ${label}` : "Nothing saved yet";
    const where = {
      db: "Saved to this page's database. The next Claude session reads it and updates the ledger.",
      server: "Saved to experiments/ear_bench/results/verdicts.json by the local server. Any session reads it there.",
    }[Store.mode] || "Saved in this browser only. Use Copy verdicts to send them to a session.";
    if (!full && box.querySelector("textarea") === document.activeElement) {
      // Keep typing undisturbed, but never let the buttons show a verdict the store doesn't hold.
      $("#verdict-status").textContent = status;
      box.querySelectorAll("[data-verdict]").forEach((btn) => {
        const k = btn.dataset.verdict;
        btn.className = `btn ${v.verdict === k ? `on v-${k}` : ""}`;
      });
      return;
    }
    box.innerHTML = `
      <div class="v-head">
        <h3>Your call on ${g.id}</h3>
        <div class="seg" role="group" aria-label="Verdict">
          ${choices.map(([k, l]) => `<button class="btn ${v.verdict === k ? `on v-${k}` : ""}" data-verdict="${k}" ${Store.readOnly ? "disabled" : ""}>${l}</button>`).join("")}
        </div>
      </div>
      <label class="label" for="verdict-notes">What you heard, and your answers to the gate's questions</label>
      <textarea id="verdict-notes" rows="3" ${Store.readOnly ? "readonly" : ""} placeholder="(a) … (b) …">${escape(v.notes || "")}</textarea>
      <p class="hint"><span id="verdict-status">${status}</span> · ${where}</p>`;
    box.querySelectorAll("[data-verdict]").forEach((b) => b.addEventListener("click", () => {
      const cur = Store.get("gates", g.id) || {};
      // Set, never toggle: clicking the verdict that is already saved must not clear it.
      if (cur.verdict === b.dataset.verdict) return;
      Store.saveGate(g.id, { verdict: b.dataset.verdict, notes: $("#verdict-notes").value });
      renderVerdict(true);
    }));
    $("#verdict-notes").addEventListener("input", (e) => {
      clearTimeout(notesTimer);
      $("#verdict-status").textContent = "Typing…";
      notesTimer = setTimeout(() => {
        const cur = Store.get("gates", g.id) || {};
        Store.saveGate(g.id, { verdict: cur.verdict || null, notes: e.target.value });
      }, 700);
    });
  }

  // ----- instrument -----
  function renderCompare() {
    const box = $("#compare");
    if (!box) return;
    const g = currentGroup();
    Compare.render(box, {
      a: scaleOf(state.a), b: scaleOf(state.b), scaleOf, escape, fmt, hz, ensureAudio, playTriad, runAThenB, phraseAThenB,
      tol: () => state.tol, hasPhrase: () => state.phrase.length > 0, readOnly: Store.readOnly,
      saved: () => Store.get("comparisons", comparisonId()),
      save: (body) => Store.saveComparison(comparisonId(), { gate: g.kind === "gate" ? g.id : null, a: state.a, b: state.b, ...body }),
    });
  }

  function renderInstrument() {
    renderCompare();
    renderInstrumentBar();
    renderStrip();
    renderActions();
    renderTriads();
    renderTable();
  }

  function renderInstrumentBar() {
    const bar = $("#inst-bar");
    if (!bar) return;
    const a = scaleOf(state.a);
    const b = scaleOf(state.b);
    const slotBtn = (slot, s) => `
      <button class="slot ${state.slot === slot ? "on" : ""}" data-slot="${slot}" ${s ? "" : "disabled"}>
        <span class="slot-k">${slot.toUpperCase()}</span>
        <span class="slot-n">${s ? escape(label(s)).replace(/_/g, "_<wbr>") : "Set a B from the list"}</span>
        <span class="slot-m">${s ? `${Tuning.model(s).n} tones` : ""}</span>
      </button>`;
    const folders = new Map();
    state.data.scales.filter((x) => !x.blind && x.protocol !== "eareps").forEach((x) => {
      const k = `${x.module}/${x.folder}`;
      folders.set(k, [...(folders.get(k) || []), x]);
    });
    const picker = [...folders.entries()].map(([k, xs]) => `<optgroup label="${escape(k)}">${xs.map((x) =>
      `<option value="${x.id}" ${x.id === state.b ? "selected" : ""}>${escape(x.name)}</option>`).join("")}</optgroup>`).join("");
    bar.innerHTML = `<div class="slots">${slotBtn("a", a)}${slotBtn("b", b)}</div>
      <div class="row bpick"><label class="label" for="bpick">B from any gate or the library</label>
        <select id="bpick"><option value="">(none)</option>${picker}</select></div>`;
    bar.querySelectorAll("[data-slot]").forEach((el) => el.addEventListener("click", () => setSlot(el.dataset.slot)));
    $("#bpick").addEventListener("change", (e) => {
      state.b = e.target.value && e.target.value !== state.a ? e.target.value : null;
      state.slot = state.b ? "b" : "a";
      renderInstrument();
      renderScales();
    });
  }

  function setSlot(slot) {
    if (slot === "b" && !state.b) return;
    state.slot = slot;
    renderInstrumentBar();
    renderStrip();
    renderTriads();
    renderTable();
  }

  function renderStrip() {
    const wrap = $("#strip-wrap");
    const s = active();
    if (!wrap || !s) { if (wrap) wrap.innerHTML = `<p class="hint">No playable scales here.</p>`; return; }
    const m = Tuning.model(s);
    const other = scaleOf(state.slot === "a" ? state.b : state.a);
    if (s.blind) {
      wrap.innerHTML = `<div class="deg-row">${Array.from({ length: m.n + 1 }, (_, i) => `<button class="deg" data-deg="${i}">${i}</button>`).join("")}</div>`;
    } else {
      const W = Math.max(640, m.n * 18);
      const x = (c) => 14 + (c / m.period) * (W - 28);
      const bars = [...m.tones, m.period].map((c, i) => `
        <g class="bar" data-deg="${i}" tabindex="0" role="button" aria-label="Degree ${i}, ${c.toFixed(1)} cents">
          <rect x="${x(c) - 7}" y="8" width="14" height="64" rx="3"></rect>
          <line x1="${x(c)}" x2="${x(c)}" y1="12" y2="68"></line>
          ${m.n <= 41 || i % 2 === 0 ? `<text x="${x(c)}" y="86">${i}</text>` : ""}
        </g>`).join("");
      const ghost = other ? (() => { const om = Tuning.model(other); return [...om.tones, om.period].map((c) => `<line class="ghost" x1="${x((c / om.period) * m.period)}" x2="${x((c / om.period) * m.period)}" y1="94" y2="104"></line>`).join(""); })() : "";
      wrap.innerHTML = `
        <svg class="strip" viewBox="0 0 ${W} 108" width="${W}" height="108" role="group" aria-label="Pitch strip, one period, 1/1 at left">
          <line class="axis" x1="14" x2="${W - 14}" y1="72" y2="72"></line>
          ${bars}
          ${ghost}
        </svg>`;
    }
    wrap.querySelectorAll("[data-deg]").forEach((el) => {
      const d = () => Number(el.dataset.deg) + state.stripOct * m.n;
      const key = `strip${el.dataset.deg}`;
      el.addEventListener("pointerdown", async (e) => { e.preventDefault(); await ensureAudio(); el.setPointerCapture && el.setPointerCapture(e.pointerId); playDegree(key, d()); });
      el.addEventListener("pointerup", () => release(key));
      el.addEventListener("pointercancel", () => release(key));
      el.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.repeat) { e.stopPropagation(); playDegree(key, d()); } });
      el.addEventListener("keyup", (e) => { if (e.key === "Enter") release(key); });
    });
    markStrip();
  }

  function markStrip(highlight) {
    const s = active();
    if (!s) return;
    const m = Tuning.model(s);
    const heldDegs = new Set([...state.held.values()].map((c) => {
      const d = Tuning.nearestDegree(m, c);
      return ((d % m.n) + m.n) % m.n;
    }));
    document.querySelectorAll("#strip-wrap [data-deg]").forEach((el) => {
      const i = Number(el.dataset.deg) % m.n;
      el.classList.toggle("held", heldDegs.has(i));
      el.classList.toggle("hl-P", !!highlight && highlight.kind === "P" && highlight.idx.has(i));
      el.classList.toggle("hl-S", !!highlight && highlight.kind === "S" && highlight.idx.has(i));
    });
  }

  function renderActions() {
    const box = $("#inst-actions");
    if (!box) return;
    const g = currentGroup();
    const cmp = state.a && state.b ? Store.get("comparisons", comparisonId()) : null;
    box.innerHTML = `
      <div class="row">
        <span class="label">Strip octave</span>
        <button class="btn sm" id="oct-dn" aria-label="Strip octave down">−</button>
        <span class="mono">${state.stripOct >= 0 ? "+" : ""}${state.stripOct}</span>
        <button class="btn sm" id="oct-up" aria-label="Strip octave up">+</button>
        <span class="sep"></span>
        <button class="btn" id="run">Scale up and down</button>
        ${active() && !active().blind ? `<button class="btn" id="tri-all">Triads in turn</button>` : ""}
        <button class="btn ${state.drone ? "on" : ""}" id="drone">Drone 1/1</button>
        <button class="btn ${state.recording ? "rec" : ""}" id="rec">${state.recording ? "Stop recording" : "Record phrase"}</button>
        <button class="btn" id="rep-a" ${state.phrase.length ? "" : "disabled"}>Replay on A</button>
        <button class="btn" id="rep-b" ${state.phrase.length && state.b ? "" : "disabled"}>Replay on B</button>
        <button class="btn" id="stop">Stop all</button>
      </div>
      ${state.a && state.b && g.kind === "gate" ? `
      <div class="row prefer">
        <span class="label">Which do you prefer?</span>
        ${[["a", "A"], ["b", "B"], ["same", "Same to me"]].map(([k, l]) => `<button class="btn sm ${cmp && cmp.prefer === k ? "on" : ""}" data-prefer="${k}" ${Store.readOnly ? "disabled" : ""}>${l}</button>`).join("")}
        ${cmp && cmp.prefer ? `<span class="hint">saved</span>` : ""}
      </div>` : ""}
      <p class="hint keys">Keys: <kbd>a</kbd> is 1/1, the rows run upward by degree (<kbd>z</kbd> row below, <kbd>q</kbd> and number rows above).
        <kbd>←</kbd><kbd>→</kbd> shift a degree, <kbd>⇧</kbd>+arrows an octave, <kbd>\`</kbd> swaps A and B, <kbd>Esc</kbd> stops.
        MIDI: note 60 is 1/1 and each key is the next degree. Key window now starts at degree ${state.offset}.</p>`;
    $("#oct-dn").onclick = () => { state.stripOct -= 1; renderActions(); };
    $("#oct-up").onclick = () => { state.stripOct += 1; renderActions(); };
    $("#run").onclick = async () => { await ensureAudio(); runScale(); };
    const ta = $("#tri-all");
    if (ta) ta.onclick = async () => { await ensureAudio(); playAllTriads(); };
    $("#drone").onclick = async () => { await ensureAudio(); toggleDrone(); renderActions(); };
    $("#rec").onclick = async () => {
      await ensureAudio();
      state.recording = !state.recording;
      if (state.recording) { state.phrase = []; state.t0 = Synth.now(); }
      renderActions();
      renderCompare();
    };
    $("#rep-a").onclick = async () => { await ensureAudio(); replayOn(state.a); };
    $("#rep-b").onclick = async () => { await ensureAudio(); replayOn(state.b); };
    $("#stop").onclick = () => { stopAll(); renderActions(); };
    box.querySelectorAll("[data-prefer]").forEach((b) => b.addEventListener("click", () => {
      const cur = Store.get("comparisons", comparisonId()) || {};
      Store.saveComparison(comparisonId(), { picks: cur.picks || {}, gate: g.id, a: state.a, b: state.b, prefer: cur.prefer === b.dataset.prefer ? null : b.dataset.prefer });
      renderActions();
    }));
  }

  function comparisonId() {
    const raw = `${state.groupId}__${state.a}__${state.b}`;
    if (raw.length <= 190) return raw;
    let h = 0;
    for (const ch of raw) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
    return `${state.groupId}__${h.toString(36)}`;
  }

  function renderTriads() {
    const box = $("#triads");
    const s = active();
    if (!box) return;
    if (!s || s.blind) { box.innerHTML = `<h3>Triads</h3><p class="hint">Hidden: this set is blinded.</p>`; return; }
    const ref = s.reference ? scaleOf(s.reference) : null;
    const viewToggle = () => (ref ? `<div class="seg sm" role="group" aria-label="Triad view">
      ${[["target", "Target triads"], ["all", "All in this scale"]].map(([k, l]) => `<button class="btn sm ${state.triadView === k ? "on" : ""}" data-view="${k}">${l}</button>`).join("")}</div>` : "");
    const controls = () => `
      <div class="row">
        <label class="label" for="tol">Tolerance</label>
        <input type="range" id="tol" min="0.25" max="12" step="0.25" value="${state.tol}">
        <span class="mono" id="tol-v">${state.tol.toFixed(2)}¢</span>
        <div class="seg sm" role="group" aria-label="Triad kinds">
          ${[["PS", "Both"], ["P", "P"], ["S", "S"]].map(([k, l]) => `<button class="btn sm ${state.kinds === k ? "on" : ""}" data-kinds="${k}">${l}</button>`).join("")}
        </div>
      </div>`;
    const bindControls = (root) => {
      const tol = $("#tol", root);
      tol.addEventListener("input", () => { state.tol = Number(tol.value); $("#tol-v", root).textContent = `${state.tol.toFixed(2)}¢`; });
      tol.addEventListener("change", renderTriads);
      root.querySelectorAll("[data-kinds]").forEach((b) => b.addEventListener("click", () => { state.kinds = b.dataset.kinds; renderTriads(); }));
      root.querySelectorAll("[data-view]").forEach((b) => b.addEventListener("click", () => { state.triadView = b.dataset.view; renderTriads(); }));
    };
    if (ref && state.triadView === "target") {
      Targets.render(box, s, ref, {
        escape, fmt, label, ensureAudio, playTriad, markStrip, viewToggle, controls, bindControls,
        tol: () => state.tol, kinds: () => state.kinds,
      });
      return;
    }
    const all = triadsFor(s);
    const shown = all.filter((t) => state.kinds.includes(t.kind));
    const nP = all.filter((t) => t.kind === "P").length;
    const nS = all.length - nP;
    box.innerHTML = `
      <div class="t-head">
        <h3>Triads in ${escape(label(s))}</h3>
        ${viewToggle()}
        <p class="hint"><span class="k-P">${nP} proportional</span> · <span class="k-S">${nS} subcontrary</span> within ${state.tol.toFixed(2)}¢ of the arithmetic or harmonic mean</p>
      </div>
      ${controls()}
      <div class="t-list" role="list">
        ${shown.slice(0, TRIAD_ROW_LIMIT).map((t, i) => `
          <button class="t-row" role="listitem" data-tri="${i}">
            <span class="kchip k-${t.kind}">${t.kind}</span>
            <span class="mono">${t.degrees.join("·")}</span>
            <span class="t-form">${t.form ? `≈ ${t.form}` : ""}</span>
            <span class="mono t-dev">${fmt(t.dev)}¢</span>
          </button>`).join("") || `<p class="hint">None at this tolerance. Widen it to see near-misses.</p>`}
        ${shown.length > TRIAD_ROW_LIMIT ? `<p class="hint">Showing the ${TRIAD_ROW_LIMIT} closest of ${shown.length}.</p>` : ""}
      </div>`;
    bindControls(box);
    const n = Tuning.model(s).n;
    box.querySelectorAll("[data-tri]").forEach((row) => {
      const t = shown[Number(row.dataset.tri)];
      const idx = new Set(t.degrees.map((d) => d % n));
      row.addEventListener("mouseenter", () => markStrip({ kind: t.kind, idx }));
      row.addEventListener("focus", () => markStrip({ kind: t.kind, idx }));
      row.addEventListener("mouseleave", () => markStrip());
      row.addEventListener("click", async () => { await ensureAudio(); playTriad(t); });
    });
  }

  function renderTable() {
    const box = $("#table");
    const s = active();
    if (!box) return;
    if (!s || s.blind) { box.innerHTML = ""; box.hidden = true; return; }
    box.hidden = false;
    const m = Tuning.model(s);
    const steps = Tuning.stepSizes(m);
    const ratios = s.ratios ? ["1/1", ...s.ratios.slice(0, -1)] : null;
    const sorted = s.ratios ? m.tones.map((c) => { const i = [0, ...s.cents.slice(0, -1)].findIndex((x) => Math.abs(x - c) < 1e-6); return ratios[i]; }) : null;
    box.innerHTML = `
      <details>
        <summary><h3>Tuning of ${escape(label(s))}</h3> <span class="hint">${m.n} tones, period ${m.period.toFixed(3)}¢${state.blindNames ? "" : ` · ${escape(s.file)}`}</span></summary>
        ${state.blindNames ? "" : `<p class="desc">${escape(s.description)}</p>`}
        <div class="tbl-wrap"><table>
          <thead><tr><th>Degree</th><th>Cents</th>${sorted ? "<th>Ratio</th>" : ""}<th>Step to next</th><th>Hz at 1/1 = ${state.baseHz.toFixed(2)}</th></tr></thead>
          <tbody>${m.tones.map((c, i) => `<tr><td>${i}</td><td>${c.toFixed(3)}</td>${sorted ? `<td>${sorted[i] || ""}</td>` : ""}<td>${steps[i].toFixed(3)}</td><td>${hz(c).toFixed(2)}</td></tr>`).join("")}</tbody>
        </table></div>
      </details>`;
  }

  // ----- scale list -----
  function renderScales() {
    const box = $("#scales");
    if (!box) return;
    if (box.contains(document.activeElement) && document.activeElement.tagName === "TEXTAREA") return;
    const g = currentGroup();
    const list = g.scales;
    const ordered = state.blindNames && state.shuffle ? [...list].sort((x, y) => state.shuffle.get(x.id) - state.shuffle.get(y.id)) : list;
    box.innerHTML = `
      <div class="s-head">
        <h3>Scales <span class="hint">${list.length}</span></h3>
        ${list.length > 1 && !list[0].blind ? `<button class="btn sm ${state.blindNames ? "on" : ""}" id="blind">${state.blindNames ? "Reveal names" : "Hide names"}</button>` : ""}
      </div>
      <div class="s-list">
        ${ordered.map((s) => {
          const r = Store.get("scales", s.id) || {};
          const isA = s.id === state.a;
          const isB = s.id === state.b;
          return `
          <article class="s-card ${isA ? "is-a" : ""} ${isB ? "is-b" : ""}">
            <div class="s-top">
              <h4>${escape(label(s)).replace(/_/g, "_<wbr>")}</h4>
              <span class="mono">${Tuning.model(s).n}</span>
            </div>
            ${state.blindNames || s.blind ? "" : `<p class="desc">${escape(s.description)}</p>`}
            <div class="row">
              <button class="btn sm ${isA ? "on" : ""}" data-as="a" data-id="${s.id}">Play as A</button>
              <button class="btn sm ${isB ? "on" : ""}" data-as="b" data-id="${s.id}">Set as B</button>
              <span class="sep"></span>
              ${[1, 2, 3, 4, 5].map((n) => `<button class="dot ${r.rating === n ? "on" : ""}" data-rate="${n}" data-id="${s.id}" aria-label="Rate ${n} of 5" ${Store.readOnly ? "disabled" : ""}>${n}</button>`).join("")}
            </div>
            <textarea class="s-note" rows="1" data-note="${s.id}" placeholder="Note on this scale" aria-label="Note on ${escape(label(s))}" ${Store.readOnly ? "readonly" : ""}>${escape(r.note || "")}</textarea>
          </article>`;
        }).join("")}
      </div>`;
    const blindBtn = $("#blind");
    if (blindBtn) blindBtn.onclick = () => {
      state.blindNames = !state.blindNames;
      if (state.blindNames) {
        const ids = list.map((s) => s.id).sort(() => Math.random() - 0.5);
        state.shuffle = new Map(ids.map((id, i) => [id, i + 1]));
      }
      renderInstrument();
      renderScales();
    };
    box.querySelectorAll("[data-as]").forEach((b) => b.addEventListener("click", () => {
      if (b.dataset.as === "a") { state.a = b.dataset.id; if (state.b === state.a) state.b = null; state.slot = "a"; }
      else { state.b = state.b === b.dataset.id ? null : b.dataset.id; if (state.b === state.a) state.b = null; state.slot = state.b ? "b" : "a"; }
      renderInstrument();
      renderScales();
    }));
    box.querySelectorAll("[data-rate]").forEach((b) => b.addEventListener("click", () => {
      const cur = Store.get("scales", b.dataset.id) || {};
      const n = Number(b.dataset.rate);
      Store.saveScale(b.dataset.id, { gate: g.kind === "gate" ? g.id : null, rating: cur.rating === n ? null : n, note: cur.note || "" });
      renderScales();
    }));
    const timers = {};
    box.querySelectorAll("[data-note]").forEach((t) => t.addEventListener("input", () => {
      clearTimeout(timers[t.dataset.note]);
      timers[t.dataset.note] = setTimeout(() => {
        const cur = Store.get("scales", t.dataset.note) || {};
        Store.saveScale(t.dataset.note, { gate: g.kind === "gate" ? g.id : null, rating: cur.rating || null, note: t.value });
      }, 700);
    }));
  }

  // ---------- inputs ----------
  function typing(e) {
    const t = e.target;
    return t && (t.tagName === "TEXTAREA" || (t.tagName === "INPUT" && t.type !== "range") || t.tagName === "SELECT");
  }

  window.addEventListener("keydown", async (e) => {
    if (typing(e) || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.code === "Escape") { stopAll(); renderActions(); Passages.stopNow(); return; }
    if (e.code === "Space" && state.spaceHold) { e.preventDefault(); if (!e.repeat) state.spaceHold.on(); return; }
    if (!active()) return;
    if (e.code === "Backquote") { setSlot(state.slot === "a" ? "b" : "a"); return; }
    if (e.code === "ArrowLeft" || e.code === "ArrowRight") {
      e.preventDefault();
      const step = e.shiftKey ? Tuning.model(active()).n : 1;
      state.offset += e.code === "ArrowLeft" ? -step : step;
      renderActions();
      return;
    }
    if (!KEY_INDEX.has(e.code) || e.repeat) return;
    e.preventDefault();
    await ensureAudio();
    playDegree(`key:${e.code}`, state.offset + KEY_INDEX.get(e.code));
  });
  window.addEventListener("keyup", (e) => {
    if (e.code === "Space" && state.spaceHold) { state.spaceHold.off(); return; }
    if (KEY_INDEX.has(e.code)) release(`key:${e.code}`);
  });
  window.addEventListener("blur", () => { Synth.allOff(); state.held.clear(); });

  async function connectMidi(fromClick = true) {
    const chip = $("#midi");
    // A click is a user gesture, so it can also start audio: MIDI notes alone never can.
    if (fromClick) await ensureAudio();
    if (!navigator.requestMIDIAccess) { chip.textContent = "MIDI: open the local bench in Chrome"; showMidiHelp(); return; }
    try {
      const access = await navigator.requestMIDIAccess();
      const bind = () => {
        const names = [];
        access.inputs.forEach((input) => { names.push(input.name); input.onmidimessage = onMidi; });
        chip.textContent = names.length ? `MIDI: ${names.join(", ")}` : "MIDI on, no inputs yet";
        Diag.setMidi({ inputs: names, error: null });
      };
      access.onstatechange = bind;
      bind();
      chip.classList.add("on");
      $("#midi-help").hidden = true;
    } catch (err) {
      Diag.setMidi({ error: String(err && err.message ? err.message : err) });
      chip.textContent = "MIDI: open the local bench";
      showMidiHelp();
    }
  }
  function showMidiHelp() {
    const box = $("#midi-help");
    const url = `http://localhost:8765/${location.hash || ""}`;
    box.hidden = false;
    const local = /^(localhost|127\.0\.0\.1)$/.test(location.hostname);
    $("#midi-why").textContent = local
      ? "The browser showing this page did not grant MIDI access. The Claude app's built-in browser pane and Safari never do."
      : "It runs inside claude.ai, which keeps pages away from USB and MIDI hardware.";
    $("#midi-url").textContent = url;
    $("#midi-copy").onclick = async () => {
      try { await navigator.clipboard.writeText(url); $("#midi-copy").textContent = "Copied"; }
      catch (e) { const r = document.createRange(); r.selectNodeContents($("#midi-url")); getSelection().removeAllRanges(); getSelection().addRange(r); $("#midi-copy").textContent = "Selected, press ⌘C"; }
    };
    $("#midi-close").onclick = () => { box.hidden = true; };
  }

  async function onMidi(msg) {
    const [st, d1, d2] = msg.data;
    const cmd = st & 0xf0;
    if (cmd === 0x90 && d2 > 0) {
      const sounding = await ensureAudio();
      Diag.noteIn(d1, sounding);
      if (!sounding) {
        $("#midi").textContent = `MIDI note ${d1} arrived. Click Start audio to hear it`;
        $("#audio").classList.add("rec");
        return;
      }
      $("#audio").classList.remove("rec");
      playDegree(`midi${d1}`, d1 - 60);
      $("#midi").textContent = `MIDI: note ${d1} → degree ${d1 - 60}`;
    }
    else if (cmd === 0x80 || (cmd === 0x90 && d2 === 0)) release(`midi${d1}`);
    else if (cmd === 0xb0 && d1 === 64) {
      state.sustain = d2 >= 64;
      if (!state.sustain) { state.sustained.forEach((k) => release(k)); state.sustained.clear(); }
    }
  }

  function bindHeader() {
    const timbre = $("#timbre");
    const opts = (set) => Object.entries(set).map(([k, t]) => `<option value="${k}">${t.label}</option>`).join("");
    timbre.innerHTML = `<optgroup label="Sustained">${opts(Timbres.SUSTAINED)}</optgroup><optgroup label="Plucked and struck">${opts(Timbres.STRUCK)}</optgroup>`;
    timbre.value = Synth.timbre;
    timbre.onchange = () => {
      Synth.setTimbre(timbre.value);
      if (currentGroup() && currentGroup().scales.some((s) => s.protocol === "eareps")) renderEps();
    };
    $("#drive").oninput = (e) => { Synth.setDrive(Number(e.target.value)); $("#drive-v").textContent = Number(e.target.value) ? Number(e.target.value).toFixed(1) : "off"; };
    $("#vol").oninput = (e) => Synth.setVolume(Number(e.target.value));
    $("#base").onchange = (e) => {
      const v = Number(e.target.value);
      if (v >= 20 && v <= 2000) { state.baseHz = v; renderTable(); } else e.target.value = state.baseHz;
    };
    $("#audio").onclick = ensureAudio;
    $("#midi").onclick = () => connectMidi(true);
    $("#copy").onclick = async () => {
      const text = Store.exportAll();
      try { await navigator.clipboard.writeText(text); $("#copy").textContent = "Copied"; }
      catch (e) { const ta = $("#export"); ta.hidden = false; ta.value = text; ta.select(); $("#copy").textContent = "Select and copy below"; }
      setTimeout(() => { $("#copy").textContent = "Copy verdicts"; }, 2500);
    };
    $("#queue").addEventListener("click", (e) => {
      const a = e.target.closest("[data-group]");
      if (!a) return;
      e.preventDefault();
      selectGroup(a.dataset.group);
      try { history.replaceState(null, "", `#${a.dataset.group}`); } catch (err) { /* sandboxed */ }
    });
  }

  function onStore(info) {
    if (info.error) { $("#store-msg").textContent = info.error; $("#store-msg").hidden = false; }
    if (info.mode) $("#store-mode").textContent = { db: "Verdicts save to this page", server: "Verdicts save to the repo (local server)" }[Store.mode] || "Verdicts save in this browser";
    renderSidebar();
    if (!state.groupId) return;
    if (info.mode && !currentGroup().scales.some((s) => s.protocol === "eareps")) { renderMain(); return; }
    if (currentGroup().scales.some((s) => s.protocol === "eareps")) {
      if ((info.collection === "eareps" || info.mode) && document.activeElement.id !== "eps-notes") renderEps();
      return;
    }
    if (info.collection === "gates") renderVerdict(false);
    if (info.collection === "scales") renderScales();
    if (info.collection === "comparisons") { renderActions(); renderCompare(); }
  }

  function armAudioOnFirstGesture() {
    // Browsers only start audio from a gesture on the page; MIDI notes never count.
    // So the first click or key anywhere starts it, and Start audio is never a trap.
    const start = () => { ensureAudio().catch(showError); };
    document.addEventListener("pointerdown", start, { once: true, capture: true });
    document.addEventListener("keydown", start, { once: true, capture: true });
  }

  function showError(err) {
    Diag.error(err && err.message ? err.message : err);
    const msg = $("#store-msg");
    msg.textContent = `Something broke: ${err && err.message ? err.message : err}. Reload the page; if it repeats, tell Claude this message.`;
    msg.hidden = false;
  }

  async function boot() {
    window.addEventListener("error", (e) => showError(e.error || e.message));
    window.addEventListener("unhandledrejection", (e) => showError(e.reason));
    armAudioOnFirstGesture();
    // The sticky now-playing strip sits just under the sticky top bar, whose height wraps with width.
    const topH = () => document.documentElement.style.setProperty("--top-h", `${document.querySelector(".top").offsetHeight}px`);
    topH();
    window.addEventListener("resize", topH);
    bindHeader();
    Store.onChange(onStore);
    try {
      const res = await fetch("data.json");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      state.data = await res.json();
    } catch (err) {
      $("#main").innerHTML = `<section class="card"><h3>Couldn't load the scale bundle</h3><p>data.json didn't load (${escape(err.message)}). If you opened the file directly, serve the folder instead: <code>python3 -m http.server -d docs/ear-bench 8765</code>.</p></section>`;
      return;
    }
    state.data.scales.forEach((s) => state.byId.set(s.id, s));
    const hash = decodeURIComponent((location.hash || "").slice(1));
    const gs = groups();
    selectGroup(gs.some((g) => g.id === hash) ? hash : (gs.find((g) => g.kind === "gate" && g.gate.state === "PENDING" && !g.scales.some((s) => s.protocol)) || gs[0]).id);
    Store.init().then(async (mode) => {
      if (mode !== "server") return;
      Diag.start(() => ({
        audio: Synth.running() ? "running" : "off", timbre: Synth.timbre, baseHz: state.baseHz,
        gate: state.groupId, a: state.a, b: state.b, slot: state.slot, store: Store.mode,
      }));
      // Reconnect MIDI on every load once Chrome has granted it, so a reload needs no click.
      try {
        const perm = navigator.permissions && await navigator.permissions.query({ name: "midi" });
        if (perm && perm.state === "granted") connectMidi(false);
      } catch (e) { /* permissions API without midi: wait for the button */ }
    });
    window.addEventListener("hashchange", () => {
      const id = decodeURIComponent(location.hash.slice(1));
      if (id && id !== state.groupId && groups().some((g) => g.id === id)) selectGroup(id);
    });
  }

  boot();
})();
