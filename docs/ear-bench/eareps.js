// EAR-eps sitting (G-025), run as experiments/lattice/EAREPS_PROTOCOL.md says:
// blocks B, A, C, D in numbered order; hold keys 60-61-62 (degrees 0, 1, 2);
// one verdict per rung, committed as you go and never revised. No cents,
// ratios or pitch display anywhere in this panel.
"use strict";

const Eareps = (() => {
  const BLOCKS = ["B", "A", "C", "D"];
  const VERDICTS = [
    ["locked", "Locked", "fuses into one in-tune sonority; steady"],
    ["beating", "Beating", "audible waver, still reads as the chord"],
    ["broken", "Broken", "the fusion is gone; reads as mistuned"],
  ];

  function order(scales) {
    const rungs = scales.filter((s) => s.protocol === "eareps");
    const blockOf = (s) => s.name.split("_")[1];
    return rungs.sort((a, b) => BLOCKS.indexOf(blockOf(a)) - BLOCKS.indexOf(blockOf(b)) || a.name.localeCompare(b.name));
  }

  function render(root, scales, ctx) {
    const rungs = order(scales);
    const sitting = Store.get("eareps", "responses") || { responses: {} };
    const responses = sitting.responses || {};
    const done = rungs.filter((r) => responses[r.name] && responses[r.name].verdict);
    const current = rungs.find((r) => !(responses[r.name] && responses[r.name].verdict));
    const draft = ctx.draft;

    root.innerHTML = `
      <section class="card protocol">
        <header class="protocol-head">
          <div>
            <p class="eyebrow">EAR-ε sitting · blinded</p>
            <h3>${current ? `Rung ${done.length + 1} of ${rungs.length}: ${current.name}` : "Sitting complete"}</h3>
          </div>
          <div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="${rungs.length}" aria-valuenow="${done.length}">
            <span style="width:${(100 * done.length) / rungs.length}%"></span>
          </div>
        </header>
        ${current ? `
        <p class="hint">Hold the chord for at least 5 seconds, release, hold again. Replay as often as you like. Space bar holds it too. Once you commit a verdict it stays committed.</p>
        ${Synth.struck ? `<p class="warn">The protocol asks for a sustained, steady patch. A plucked or struck timbre decays while you hold the chord, so switch to Reed or Organ for this sitting.</p>` : ""}
        <div class="row">
          <button class="btn primary big" id="eps-hold" aria-describedby="eps-hold-hint">Hold chord</button>
          <button class="btn" id="eps-five">Play 5 s</button>
          <span class="hint" id="eps-hold-hint">keys 60-61-62 of ${current.name}</span>
        </div>
        <fieldset class="verdicts">
          <legend>Verdict</legend>
          ${VERDICTS.map(([v, label, hint]) => `
            <label class="choice ${draft.verdict === v ? "on" : ""}">
              <input type="radio" name="eps-verdict" value="${v}" ${draft.verdict === v ? "checked" : ""}>
              <strong>${label}</strong><span>${hint}</span>
            </label>`).join("")}
        </fieldset>
        <div class="row">
          <span class="label">Fusion (optional)</span>
          ${[1, 2, 3, 4, 5].map((n) => `<button class="dot ${draft.fusion === n ? "on" : ""}" data-fusion="${n}" aria-label="Fusion ${n} of 5">${n}</button>`).join("")}
        </div>
        <label class="label" for="eps-notes">Notes</label>
        <textarea id="eps-notes" rows="2" placeholder="Anything you heard">${ctx.escape(draft.notes || "")}</textarea>
        <div class="row">
          <button class="btn primary" id="eps-commit" ${draft.verdict && !Store.readOnly && !Synth.struck ? "" : "disabled"}>Commit and go to next rung</button>
          ${sitting.synth_patch && sitting.synth_patch !== Synth.describe()
            ? `<span class="warn">The sitting started on "${ctx.escape(sitting.synth_patch)}". The protocol asks for the same patch on every rung.</span>` : ""}
        </div>` : `
        <p>All ${rungs.length} verdicts are saved. Tell any session "EAR-ε responses are in" and it writes
        <code>results/eareps_responses.json</code> from this page, then unseals the key and runs the pre-registered analysis.</p>`}
        ${done.length ? `<details class="committed"><summary>${done.length} committed</summary>
          <ol>${done.map((r) => `<li><span class="mono">${r.name}</span> ${responses[r.name].verdict}${responses[r.name].fusion_1to5 ? ` · fusion ${responses[r.name].fusion_1to5}` : ""}</li>`).join("")}</ol>
        </details>` : ""}
      </section>`;

    if (!current) return;
    const chord = () => {
      const m = Tuning.model(current);
      return [0, 1, 2].map((d) => ctx.hz(Tuning.degreeCents(m, d)));
    };
    const hold = root.querySelector("#eps-hold");
    const on = async () => { await ctx.ensureAudio(); chord().forEach((hz, i) => Synth.noteOn(`eps${i}`, hz)); hold.classList.add("down"); };
    const off = () => { [0, 1, 2].forEach((i) => Synth.noteOff(`eps${i}`)); hold.classList.remove("down"); };
    hold.addEventListener("pointerdown", (e) => { e.preventDefault(); hold.setPointerCapture(e.pointerId); on(); });
    hold.addEventListener("pointerup", off);
    hold.addEventListener("pointercancel", off);
    ctx.setSpaceHold(on, off);
    root.querySelector("#eps-five").addEventListener("click", async () => {
      await ctx.ensureAudio();
      const t = Synth.now() + 0.05;
      chord().forEach((hz) => Synth.blip(hz, t, 5));
    });
    root.querySelectorAll("input[name=eps-verdict]").forEach((el) =>
      el.addEventListener("change", () => ctx.setDraft({ ...ctx.draft, verdict: el.value })));
    root.querySelectorAll("[data-fusion]").forEach((el) =>
      el.addEventListener("click", () => {
        const n = Number(el.dataset.fusion);
        ctx.setDraft({ ...ctx.draft, fusion: ctx.draft.fusion === n ? null : n });
      }));
    root.querySelector("#eps-notes").addEventListener("input", (e) => { ctx.draft = { ...ctx.draft, notes: e.target.value }; });
    root.querySelector("#eps-commit").addEventListener("click", () => {
      const d = ctx.draft;
      const next = {
        sitting_date: sitting.sitting_date || new Date().toLocaleDateString("en-CA"),
        synth_patch: sitting.synth_patch || Synth.describe(),
        playback_chain: sitting.playback_chain || `Ear Bench browser synth, 1/1 = ${ctx.baseHz().toFixed(2)} Hz`,
        responses: {
          ...responses,
          [current.name]: { verdict: d.verdict, fusion_1to5: d.fusion || null, notes: d.notes || "", committedAt: new Date().toISOString() },
        },
      };
      off();
      ctx.setDraft({ verdict: null, fusion: null, notes: "" }, false);
      Store.saveEareps(next);
    });
  }

  return { render, order };
})();
