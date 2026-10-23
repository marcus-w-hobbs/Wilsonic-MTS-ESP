// Ear Bench diagnostics: when the page is served by the local bench server,
// it reports its own state (browser, audio, MIDI inputs, notes in and heard,
// errors) every two seconds to /api/status, so a Claude session can see what
// the open page is doing without asking for screenshots.
"use strict";

const Diag = (() => {
  const client = `page-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
  const MAX_ERRORS = 5;
  let midi = { supported: !!navigator.requestMIDIAccess, inputs: [], error: null };
  let notes = { received: 0, sounded: 0, last: null };
  let errors = [];
  let timer = null;
  let build = null;

  const setMidi = (patch) => { midi = { ...midi, ...patch }; };
  const noteIn = (note, sounded) => {
    notes = {
      received: notes.received + 1,
      sounded: notes.sounded + (sounded ? 1 : 0),
      last: { note, sounded, at: new Date().toISOString() },
    };
  };
  const error = (msg) => { errors = [...errors, { msg: String(msg), at: new Date().toISOString() }].slice(-MAX_ERRORS); };

  function browserName() {
    const ua = navigator.userAgent;
    if (/Electron|Claude/i.test(ua)) return "Claude app browser pane";
    if (/Edg\//.test(ua)) return "Edge";
    if (/Chrome\//.test(ua)) return "Chrome";
    if (/Safari\//.test(ua)) return "Safari";
    if (/Firefox\//.test(ua)) return "Firefox";
    return ua.slice(0, 80);
  }

  function report(snapshot) {
    const body = JSON.stringify({
      client, at: new Date().toISOString(), browser: browserName(), href: location.href,
      visible: document.visibilityState, focused: document.hasFocus(),
      midi, notes, errors, ...snapshot(),
    });
    fetch("api/status", { method: "POST", headers: { "Content-Type": "application/json" }, body })
      .then((res) => res.json())
      .then(({ build: next }) => {
        // The server's build id changes when a page file changes: reload to pick up the fix.
        if (!next) return;
        if (build && next !== build) location.reload();
        build = next;
      })
      .catch(() => {});
  }

  // Only the local server has /api/status; claude.ai and file:// never start this.
  function start(snapshot) {
    if (timer) return;
    report(snapshot);
    timer = setInterval(() => report(snapshot), 2000);
  }

  return { start, setMidi, noteIn, error };
})();
