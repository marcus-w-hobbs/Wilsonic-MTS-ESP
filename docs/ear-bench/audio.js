// Ear Bench synth: steady additive voices (no vibrato, chorus or detune, per
// the EAR-eps protocol), an optional ear-nonlinearity stage that makes sum
// and difference tones audible, and a compressor to keep chords from clipping.
"use strict";

const Synth = (() => {
  const TIMBRES = {
    reed: { label: "Reed (all partials, 1/n)", partials: Array.from({ length: 16 }, (_, i) => 1 / (i + 1)) },
    organ: { label: "Organ (drawbars 1-2-3-4-6-8)", partials: [1, 0.7, 0.5, 0.35, 0, 0.25, 0, 0.18] },
    clarinet: { label: "Clarinet (odd partials)", partials: Array.from({ length: 15 }, (_, i) => (i % 2 === 0 ? 1 / (i + 1) : 0)) },
    sine: { label: "Sine (control: hides combination tones)", partials: [1] },
  };
  const VOICE_GAIN = 0.16;
  const ATTACK = 0.02;
  const RELEASE = 0.28;

  let ctx = null;
  let bus = null;
  let shaper = null;
  let out = null;
  let wave = null;
  let timbre = "reed";
  let drive = 0;
  let volume = 0.8;
  const voices = new Map();

  function shaperCurve(k) {
    const n = 2048;
    const curve = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      const x = (i / (n - 1)) * 2 - 1;
      // tanh plus a small even-order term: the even term is what yields difference tones.
      curve[i] = k <= 0 ? x : (Math.tanh(k * x) + 0.25 * k * x * x) / (Math.tanh(k) + 0.25 * k);
    }
    return curve;
  }

  function buildWave() {
    const amps = TIMBRES[timbre].partials;
    const real = new Float32Array(amps.length + 1);
    const imag = new Float32Array(amps.length + 1);
    amps.forEach((a, i) => { imag[i + 1] = a; });
    wave = ctx.createPeriodicWave(real, imag);
  }

  async function start() {
    if (!ctx) {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      bus = ctx.createGain();
      shaper = ctx.createWaveShaper();
      shaper.oversample = "4x";
      const comp = ctx.createDynamicsCompressor();
      comp.threshold.value = -10;
      comp.ratio.value = 4;
      out = ctx.createGain();
      out.gain.value = volume;
      bus.connect(shaper).connect(comp).connect(out).connect(ctx.destination);
      shaper.curve = shaperCurve(drive);
      buildWave();
    }
    if (ctx.state !== "running") await ctx.resume();
    return ctx.state === "running";
  }

  const running = () => !!ctx && ctx.state === "running";

  function noteOn(key, hz, when = 0) {
    if (!ctx) return;
    noteOff(key);
    const t = Math.max(ctx.currentTime, when || ctx.currentTime);
    const osc = ctx.createOscillator();
    osc.setPeriodicWave(wave);
    osc.frequency.setValueAtTime(hz, t);
    const env = ctx.createGain();
    env.gain.setValueAtTime(0, t);
    env.gain.linearRampToValueAtTime(VOICE_GAIN, t + ATTACK);
    osc.connect(env).connect(bus);
    osc.start(t);
    voices.set(key, { osc, env });
  }

  function noteOff(key, when = 0) {
    const v = voices.get(key);
    if (!v || !ctx) return;
    voices.delete(key);
    const t = Math.max(ctx.currentTime, when || ctx.currentTime);
    v.env.gain.cancelScheduledValues(t);
    v.env.gain.setValueAtTime(v.env.gain.value, t);
    v.env.gain.linearRampToValueAtTime(0, t + RELEASE);
    v.osc.stop(t + RELEASE + 0.05);
  }

  function allOff() { [...voices.keys()].forEach((k) => noteOff(k)); }

  // Fire-and-forget scheduled note (sequences, chords).
  function blip(hz, startAt, dur) {
    const key = `blip:${Math.random()}`;
    noteOn(key, hz, startAt);
    const v = voices.get(key);
    voices.delete(key);
    const end = startAt + dur;
    v.env.gain.setValueAtTime(VOICE_GAIN, end);
    v.env.gain.linearRampToValueAtTime(0, end + RELEASE);
    v.osc.stop(end + RELEASE + 0.05);
    return key;
  }

  const now = () => (ctx ? ctx.currentTime : 0);

  function setTimbre(name) {
    if (!TIMBRES[name]) return;
    timbre = name;
    if (ctx) buildWave();
  }
  function setDrive(k) {
    drive = k;
    if (shaper) shaper.curve = shaperCurve(k);
  }
  function setVolume(v) {
    volume = v;
    if (out) out.gain.setTargetAtTime(v, ctx.currentTime, 0.02);
  }
  const describe = () => `${TIMBRES[timbre].label}; nonlinearity ${drive ? drive.toFixed(1) : "off"}`;

  return { TIMBRES, start, running, noteOn, noteOff, allOff, blip, now, setTimbre, setDrive, setVolume, describe,
    get timbre() { return timbre; } };
})();
