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
  let timbre = Timbres.JUDGING;
  let drive = 0;
  let volume = 0.8;
  let octave = 0;
  // Shared transposition (cents) wired into every live oscillator's detune, so
  // an octave step moves sounding and already-scheduled notes at once.
  let transposer = null;
  const OCTAVE_RANGE = 3;
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
      // iOS mutes Web Audio under the silent switch unless the page asks for a playback session (Safari 17+).
      try { if (navigator.audioSession) navigator.audioSession.type = "playback"; } catch (e) { /* older Safari */ }
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
      transposer = ctx.createConstantSource();
      transposer.offset.value = octave * 1200;
      transposer.start();
    }
    // Without a user gesture resume() can stay pending forever; never let a caller hang on it.
    if (ctx.state !== "running") await Promise.race([ctx.resume(), new Promise((r) => setTimeout(r, 250))]);
    return ctx.state === "running";
  }

  const running = () => !!ctx && ctx.state === "running";
  const safeStop = (osc, t) => { try { osc.stop(t); } catch (e) { /* already stopped */ } };

  // A held, steady voice: one periodic wave at a constant level.
  function sustainedVoice(c, dest, hz, t, level = 1) {
    const peak = VOICE_GAIN * level;
    const osc = c.createOscillator();
    osc.setPeriodicWave(c === ctx ? wave : waveFor(c));
    if (c === ctx && transposer) transposer.connect(osc.detune);
    osc.frequency.setValueAtTime(hz, t);
    const env = c.createGain();
    env.gain.setValueAtTime(0, t);
    env.gain.linearRampToValueAtTime(peak, t + ATTACK);
    osc.connect(env).connect(dest);
    osc.start(t);
    return {
      // Live retargeting: jump to a new pitch now (or on a note not yet started, from its start).
      setHz(next, at) {
        osc.frequency.cancelScheduledValues(at);
        osc.frequency.setValueAtTime(next, at);
      },
      stop(at) {
        env.gain.cancelScheduledValues(at);
        // .value reads the param's default (1) until the audio thread runs, so
        // clamp it: a release scheduled ahead must never jump above the voice level.
        env.gain.setValueAtTime(Math.min(env.gain.value, peak), at);
        env.gain.linearRampToValueAtTime(0, at + RELEASE);
        safeStop(osc, at + RELEASE + 0.05);
      },
    };
  }

  // A plucked or hammered voice: one sine per partial, each decaying on its
  // own time constant; releasing the key damps the whole string.
  function struckVoice(c, dest, hz, t, level = 1) {
    const spec = Timbres.STRUCK[timbre];
    // Leave headroom for one live octave step up, so partials stay below Nyquist.
    const top = 20000 / (hz * Math.pow(2, Math.max(0, octave + 1)));
    const all = spec.partials(hz);
    const partials = all.filter((p, i) => i === 0 || p.ratio <= top);
    const norm = (level * STRUCK_GAIN) / Math.sqrt(partials.reduce((s, p) => s + p.amp * p.amp, 0));
    const damper = c.createGain();
    damper.connect(dest);
    const oscs = partials.map((p) => {
      const osc = c.createOscillator();
      osc.frequency.setValueAtTime(hz * p.ratio, t);
      if (c === ctx && transposer) transposer.connect(osc.detune);
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
      setHz(next, at) {
        oscs.forEach((o, i) => {
          o.frequency.cancelScheduledValues(at);
          o.frequency.setValueAtTime(next * partials[i].ratio, at);
        });
      },
      stop(at) {
        damper.gain.setTargetAtTime(0, at, spec.damp);
        oscs.forEach((o) => safeStop(o, at + 6 * spec.damp));
      },
    };
  }

  function makeVoice(hz, t, c = ctx, dest = bus, level = 1) {
    return Timbres.isStruck(timbre) ? struckVoice(c, dest, hz, t, level) : sustainedVoice(c, dest, hz, t, level);
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

  // Scheduled notes (sequences, chords, passages) stay stoppable until they end.
  let scheduled = [];

  // Long passages (a whole eikosany's chorale is ~2000 notes, ~10 oscillators
  // each) are fed to the graph a little ahead of the playhead: building them
  // all on the tap stalls a phone past the first notes' start times, and the
  // audio thread then carries tens of thousands of waiting voices.
  const AHEAD = 2;
  let streams = [];
  let pump = 0;

  function feed() {
    if (!ctx) return;
    const until = ctx.currentTime + AHEAD;
    streams = streams.map((s) => {
      let i = s.next;
      for (; i < s.notes.length && s.notes[i].start < until; i++) {
        const n = s.notes[i];
        blip(n.hz, n.start, n.dur, n.level, n.tag);
      }
      return { ...s, next: i };
    }).filter((s) => s.next < s.notes.length);
    if (!streams.length && pump) { clearInterval(pump); pump = 0; }
  }

  // notes: [{ hz, start, dur, level, tag }] in context time; stopped by allOff.
  function stream(notes) {
    if (!ctx || !notes.length) return;
    streams = [...streams, { notes: [...notes].sort((p, q) => p.start - q.start), next: 0 }];
    feed();
    if (streams.length && !pump) pump = setInterval(feed, 250);
  }

  function allOff() {
    streams = [];
    if (pump) { clearInterval(pump); pump = 0; }
    [...voices.keys()].forEach((k) => noteOff(k));
    const t = ctx ? ctx.currentTime : 0;
    scheduled.filter((s) => s.end > t).forEach((s) => s.voice.stop(t));
    scheduled = [];
  }

  // `tag` names what the note is musically (chord i voice v, tune step, ...),
  // so a live switch can say what the same note becomes under new settings.
  function blip(hz, startAt, dur, level = 1, tag = null) {
    if (!ctx) return;
    // Struck notes ring a little past a short sequence step, as a played string would.
    const end = startAt + (Timbres.isStruck(timbre) ? Math.max(dur, 0.9) : dur);
    const voice = makeVoice(hz, startAt, ctx, bus, level);
    voice.stop(end);
    const t = ctx.currentTime;
    scheduled = [...scheduled.filter((s) => s.end > t), { voice, start: startAt, end, hz, tag }];
  }

  // Live retargeting. `map(note)` returns the new frequency for a sounding
  // tagged note, or null to leave it. The jump is immediate, by design: Ear
  // Bench measures the change, it does not smooth it.
  function retuneSounding(map) {
    if (!ctx) return 0;
    const t = ctx.currentTime;
    let moved = 0;
    scheduled = scheduled.map((s) => {
      if (!(s.start <= t && s.end > t && s.tag)) return s;
      const next = map(s);
      if (!next) return s;
      s.voice.setHz(next, t);
      moved += 1;
      return { ...s, hz: next };
    });
    return moved;
  }

  // Drop tagged notes that have not started yet; the caller reschedules.
  function cancelPending() {
    if (!ctx) return 0;
    const t = ctx.currentTime;
    const pending = scheduled.filter((s) => s.start > t && s.tag);
    pending.forEach((s) => s.voice.stop(t));
    scheduled = scheduled.filter((s) => !(s.start > t && s.tag));
    return pending.length;
  }

  // A held key or MIDI note follows a new scale.
  function retuneKey(key, next) {
    const v = voices.get(key);
    if (v && ctx) v.setHz(next, ctx.currentTime);
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
  function setOctave(n) {
    octave = Math.max(-OCTAVE_RANGE, Math.min(OCTAVE_RANGE, Math.round(n)));
    if (transposer) transposer.offset.setTargetAtTime(octave * 1200, ctx.currentTime, 0.008);
    return octave;
  }
  function setVolume(v) {
    volume = v;
    if (out) out.gain.setTargetAtTime(v, ctx.currentTime, 0.02);
  }
  const describe = () => `${Timbres.ALL[timbre].label}; nonlinearity ${drive ? drive.toFixed(1) : "off"}`;

  return { start, running, noteOn, noteOff, allOff, blip, stream, now, setTimbre, setDrive, setVolume, setOctave, describe, renderNote, OCTAVE_RANGE,
    retuneSounding, cancelPending, retuneKey,
    get octave() { return octave; },
    get timbre() { return timbre; },
    get struck() { return Timbres.isStruck(timbre); } };
})();
