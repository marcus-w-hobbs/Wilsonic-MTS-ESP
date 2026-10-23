// Ear Bench timbres. "Sustained" timbres are one periodic wave held at a
// steady level (what the EAR-eps protocol asks for). "Struck" timbres are
// built partial by partial, each with its own decay, so the brightness dies
// away the way a plucked or hammered string does. Every fundamental stays
// exactly on the scale's pitch; only the piano stretches its upper partials.
"use strict";

const Timbres = (() => {
  const harmonics = (count, amp) => Array.from({ length: count }, (_, i) => amp(i + 1));

  // Partial n of a string plucked or struck at fraction `pos` of its length.
  const pluckShape = (n, pos) => Math.abs(Math.sin(n * Math.PI * pos));

  // Struck partials: [{ratio, amp, tau}] for a fundamental hz. tau is the
  // exponential time constant in seconds; higher notes ring for less time.
  function series({ count, amp, tau, stretch = 0 }) {
    return (hz) => {
      const reg = Math.pow(261.6256 / hz, 0.35);
      const out = [];
      for (let n = 1; n <= count; n++) {
        const ratio = stretch ? (n * Math.sqrt(1 + stretch * n * n)) / Math.sqrt(1 + stretch) : n;
        if (ratio * hz > 14000) break;
        const a = amp(n);
        if (a > 1e-4) out.push({ ratio, amp: a, tau: tau(n) * reg });
      }
      return out;
    };
  }

  const SUSTAINED = {
    reed: { label: "Reed (all partials, 1/n)", partials: harmonics(16, (n) => 1 / n) },
    organ: { label: "Organ (drawbars 1-2-3-4-6-8)", partials: [1, 0.7, 0.5, 0.35, 0, 0.25, 0, 0.18] },
    clarinet: { label: "Clarinet (odd partials)", partials: harmonics(15, (n) => (n % 2 ? 1 / n : 0)) },
    sine: { label: "Sine (control: hides combination tones)", partials: [1] },
  };

  const STRUCK = {
    guitar: {
      label: "Acoustic guitar (plucked steel string)",
      attack: 0.002, damp: 0.09,
      partials: series({ count: 20, amp: (n) => pluckShape(n, 0.18) / Math.pow(n, 1.3), tau: (n) => 2.4 / (1 + 0.45 * (n - 1)) }),
    },
    electric: {
      label: "Electric guitar (clean, bridge pickup)",
      attack: 0.002, damp: 0.07,
      partials: series({ count: 24, amp: (n) => (pluckShape(n, 0.13) * (0.35 + pluckShape(n, 0.09))) / Math.pow(n, 0.9), tau: (n) => 5 / (1 + 0.25 * (n - 1)) }),
    },
    piano: {
      label: "Piano (hammered, slightly stretched partials)",
      attack: 0.003, damp: 0.12,
      partials: series({ count: 18, amp: (n) => Math.exp(-(n - 1) / 6) / Math.pow(n, 0.8), tau: (n) => 4.5 / (1 + 0.3 * (n - 1)), stretch: 0.00035 }),
    },
    epiano: {
      label: "Electric piano (tine and bark)",
      attack: 0.003, damp: 0.18,
      partials: (hz) => {
        const reg = Math.pow(261.6256 / hz, 0.35);
        return [[1, 1, 3.2], [2, 0.32, 1.1], [3, 0.12, 0.5], [4, 0.06, 0.35], [7, 0.22, 0.06], [11, 0.08, 0.03]]
          .filter(([ratio]) => ratio * hz < 14000)
          .map(([ratio, amp, tau]) => ({ ratio, amp, tau: tau * reg }));
      },
    },
  };

  const ALL = { ...SUSTAINED, ...STRUCK };
  const isStruck = (name) => Object.prototype.hasOwnProperty.call(STRUCK, name);

  return { SUSTAINED, STRUCK, ALL, isStruck };
})();
