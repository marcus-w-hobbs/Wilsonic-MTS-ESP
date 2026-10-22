// Ear Bench synth: steady or struck additive voices (no vibrato, chorus or
// detune), an optional ear-nonlinearity stage that makes sum and difference
// tones audible, and a compressor to keep chords from clipping.
"use strict";

const Synth = (() => {
  const VOICE_GAIN = 0.16;
  const STRUCK_GAIN = 0.2;
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

  function waveFor(c) {
    const t = Timbres.SUSTAINED[timbre];
    if (!t) return null;
    const amps = t.partials;
    const real = new Float32Array(amps.length + 1);
    const imag = new Float32Array(amps.length + 1);
    amps.forEach((a, i) => { imag[i + 1] = a; });
    return c.createPeriodicWave(real, imag);
  }
  function buildWave() { wave = waveFor(ctx); }

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
  const safeStop = (osc, t) => { try { osc.stop(t); } catch (e) { /* already stopped */ } };

  // A held, steady voice: one periodic wave at a constant level.
  function sustainedVoice(c, dest, hz, t) {
    const osc = c.createOscillator();
    osc.setPeriodicWave(c === ctx ? wave : waveFor(c));
    osc.frequency.setValueAtTime(hz, t);
    const env = c.createGain();
    env.gain.setValueAtTime(0, t);
    env.gain.linearRampToValueAtTime(VOICE_GAIN, t + ATTACK);
    osc.connect(env).connect(dest);
    osc.start(t);
    return {
      stop(at) {
        env.gain.cancelScheduledValues(at);
        // .value reads the param's default (1) until the audio thread runs, so
        // clamp it: a release scheduled ahead must never jump above the voice level.
        env.gain.setValueAtTime(Math.min(env.gain.value, VOICE_GAIN), at);
        env.gain.linearRampToValueAtTime(0, at + RELEASE);
        safeStop(osc, at + RELEASE + 0.05);
      },
    };
  }

  // A plucked or hammered voice: one sine per partial, each decaying on its
  // own time constant; releasing the key damps the whole string.
  function struckVoice(c, dest, hz, t) {
    const spec = Timbres.STRUCK[timbre];
    const partials = spec.partials(hz);
    const norm = STRUCK_GAIN / Math.sqrt(partials.reduce((s, p) => s + p.amp * p.amp, 0));
    const damper = c.createGain();
    damper.connect(dest);
    const oscs = partials.map((p) => {
      const osc = c.createOscillator();
      osc.frequency.setValueAtTime(hz * p.ratio, t);
      const g = c.createGain();
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(p.amp * norm, t + spec.attack);
      g.gain.setTargetAtTime(0, t + spec.attack, p.tau);
      osc.connect(g).connect(damper);
      osc.start(t);
      safeStop(osc, t + spec.attack + 7 * p.tau);
      return osc;
    });
    return {
      stop(at) {
        damper.gain.setTargetAtTime(0, at, spec.damp);
        oscs.forEach((o) => safeStop(o, at + 6 * spec.damp));
      },
    };
  }

  function makeVoice(hz, t, c = ctx, dest = bus) {
    return Timbres.isStruck(timbre) ? struckVoice(c, dest, hz, t) : sustainedVoice(c, dest, hz, t);
  }

  // One note of the current timbre rendered offline, dry (no shaper or
  // compressor): the hook the timbre measurements use.
  async function renderNote(hz, seconds, holdSeconds, sampleRate = 48000) {
    const off = new OfflineAudioContext(1, Math.ceil(seconds * sampleRate), sampleRate);
    makeVoice(hz, 0, off, off.destination).stop(holdSeconds);
    return { samples: (await off.startRendering()).getChannelData(0), sampleRate };
  }

  function noteOn(key, hz, when = 0) {
    if (!ctx) return;
    noteOff(key);
    const t = Math.max(ctx.currentTime, when || ctx.currentTime);
    voices.set(key, makeVoice(hz, t));
  }

  function noteOff(key, when = 0) {
    const v = voices.get(key);
    if (!v || !ctx) return;
    voices.delete(key);
    v.stop(Math.max(ctx.currentTime, when || ctx.currentTime));
  }

  function allOff() { [...voices.keys()].forEach((k) => noteOff(k)); }

  // Fire-and-forget scheduled note (sequences, chords).
  function blip(hz, startAt, dur) {
    if (!ctx) return;
    // Struck notes ring a little past a short sequence step, as a played string would.
    makeVoice(hz, startAt).stop(startAt + (Timbres.isStruck(timbre) ? Math.max(dur, 0.9) : dur));
  }

  const now = () => (ctx ? ctx.currentTime : 0);

  function setTimbre(name) {
    if (!Timbres.ALL[name]) return;
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
  const describe = () => `${Timbres.ALL[timbre].label}; nonlinearity ${drive ? drive.toFixed(1) : "off"}`;

  return { start, running, noteOn, noteOff, allOff, blip, now, setTimbre, setDrive, setVolume, describe, renderNote,
    get timbre() { return timbre; },
    get struck() { return Timbres.isStruck(timbre); } };
})();
