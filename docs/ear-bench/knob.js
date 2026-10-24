// Ear Bench rotary dial: a compact stand-in for a horizontal slider.
// Drag up or down to turn (Shift for fine), scroll the wheel, or use the
// arrow, Page, Home and End keys; double-click restores the default.
// It is an ARIA slider, so screen readers and keyboards treat it as one.
"use strict";

const Knob = (() => {
  const SWEEP = 270;
  const START = -135;

  const polar = (r, deg) => {
    const a = ((deg - 90) * Math.PI) / 180;
    return [20 + r * Math.cos(a), 20 + r * Math.sin(a)];
  };
  const arc = (r, from, to) => {
    const [x0, y0] = polar(r, from);
    const [x1, y1] = polar(r, to);
    return `M ${x0.toFixed(2)} ${y0.toFixed(2)} A ${r} ${r} 0 ${to - from > 180 ? 1 : 0} 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`;
  };

  function create(el, { min, max, step, value, label, format, onInput }) {
    const initial = value;
    let current = value;
    el.classList.add("knob");
    el.setAttribute("role", "slider");
    el.setAttribute("tabindex", "0");
    el.setAttribute("aria-label", label);
    el.setAttribute("aria-valuemin", String(min));
    el.setAttribute("aria-valuemax", String(max));
    el.innerHTML = `
      <svg viewBox="0 0 40 40" width="34" height="34" aria-hidden="true">
        <path class="k-track" d="${arc(15, START, START + SWEEP)}"></path>
        <path class="k-fill" d=""></path>
        <line class="k-ptr" x1="20" y1="20" x2="20" y2="8"></line>
      </svg>
      <span class="k-text"><span class="k-label">${label}</span><span class="k-val mono"></span></span>`;
    const fill = el.querySelector(".k-fill");
    const ptr = el.querySelector(".k-ptr");
    const out = el.querySelector(".k-val");

    function paint() {
      const frac = (current - min) / (max - min);
      const deg = START + frac * SWEEP;
      fill.setAttribute("d", frac > 0.002 ? arc(15, START, deg) : "");
      const [x, y] = polar(12, deg);
      ptr.setAttribute("x2", x.toFixed(2));
      ptr.setAttribute("y2", y.toFixed(2));
      const text = format(current);
      out.textContent = text;
      el.setAttribute("aria-valuenow", String(current));
      el.setAttribute("aria-valuetext", text);
    }

    function set(v) {
      const snapped = Math.round(Math.max(min, Math.min(max, v)) / step) * step;
      const next = Number(snapped.toFixed(6));
      if (next === current) return;
      current = next;
      paint();
      onInput(current);
    }

    let drag = null;
    el.addEventListener("pointerdown", (e) => {
      el.setPointerCapture(e.pointerId);
      drag = { y: e.clientY, v: current };
      e.preventDefault();
      el.focus();
    });
    el.addEventListener("pointermove", (e) => {
      if (!drag) return;
      const span = (max - min) * (e.shiftKey ? 0.25 : 1);
      set(drag.v + ((drag.y - e.clientY) / 160) * span);
    });
    const end = () => { drag = null; };
    el.addEventListener("pointerup", end);
    el.addEventListener("pointercancel", end);
    el.addEventListener("wheel", (e) => {
      e.preventDefault();
      set(current + (e.deltaY < 0 ? step : -step) * (e.shiftKey ? 1 : 2));
    }, { passive: false });
    el.addEventListener("dblclick", () => set(initial));
    el.addEventListener("keydown", (e) => {
      const moves = { ArrowUp: step, ArrowRight: step, ArrowDown: -step, ArrowLeft: -step, PageUp: step * 10, PageDown: -step * 10 };
      if (e.key in moves) set(current + moves[e.key]);
      else if (e.key === "Home") set(min);
      else if (e.key === "End") set(max);
      else return;
      // Keep the bench's own key handling (degree window, notes) out of it.
      e.preventDefault();
      e.stopPropagation();
    });

    paint();
    return { set, get: () => current };
  }

  return { create };
})();
