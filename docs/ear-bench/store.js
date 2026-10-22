// Ear Bench verdict store. On claude.ai the page's shared database holds every
// verdict, so a later Claude session can read them and update GATES.md.
// Anywhere else (a local copy of docs/) it falls back to this browser's
// localStorage, with a copy-as-JSON export.
//
// Documents:
//   gates/<G-NNN>              {verdict, notes, updatedAt}
//   scales/<scaleId>           {gate, rating, note, updatedAt}
//   comparisons/<id>           {gate, a, b, prefer, note, updatedAt}
//   eareps/responses           EAR-eps sitting, shaped like eareps_responses.template.json
"use strict";

const Store = (() => {
  const LOCAL_KEY = "earbench.v1";
  const listeners = new Set();
  let db = null;
  let mode = "starting";
  let readOnly = false;
  const cache = { gates: {}, scales: {}, comparisons: {}, eareps: {} };
  const queues = new Map();

  const emit = (info) => listeners.forEach((fn) => fn(info));
  const onChange = (fn) => { listeners.add(fn); return () => listeners.delete(fn); };

  function loadLocal() {
    try {
      const raw = localStorage.getItem(LOCAL_KEY);
      if (raw) Object.assign(cache, JSON.parse(raw));
    } catch (e) { /* storage blocked: keep the in-memory cache */ }
  }
  function saveLocal() {
    try { localStorage.setItem(LOCAL_KEY, JSON.stringify(cache)); } catch (e) { /* ignore */ }
  }

  function subscribe(collection) {
    db.collection(collection).onSnapshot(
      (snap) => {
        const next = {};
        snap.docs.forEach((d) => { next[d.id] = d.data(); });
        cache[collection] = next;
        emit({ collection });
      },
      (err) => emit({ error: `Live updates stopped (${err.code}). Reload the page to reconnect.` }),
    );
  }

  async function init() {
    loadLocal();
    const use = window.claude && window.claude.use;
    const handle = use ? await window.claude.use("db").catch(() => null) : null;
    if (handle) {
      db = handle;
      mode = "db";
      const user = await window.claude.use("user").catch(() => null);
      if (user && user.can) readOnly = (await user.can("data.write")) === false;
      ["gates", "scales", "comparisons", "eareps"].forEach(subscribe);
    } else {
      mode = "local";
    }
    emit({ mode });
    return mode;
  }

  // One write in flight per document; the latest body wins.
  function write(collection, id, body) {
    cache[collection] = { ...cache[collection], [id]: body };
    emit({ collection, saving: true });
    if (mode !== "db") { saveLocal(); emit({ collection, saved: true }); return Promise.resolve(); }
    const key = `${collection}/${id}`;
    const q = queues.get(key) || { busy: false, next: null };
    queues.set(key, q);
    q.next = body;
    if (q.busy) return Promise.resolve();
    const pump = async () => {
      q.busy = true;
      while (q.next) {
        const payload = q.next;
        q.next = null;
        try {
          await db.doc(key).set(payload);
          emit({ collection, saved: true });
        } catch (err) {
          if (err.code === "invalid_argument") readOnly = true;
          emit({ error: err.code === "invalid_argument"
            ? "This view can't save verdicts (read-only access)."
            : `Not saved (${err.code}). Your text is still here; change it again to retry.` });
        }
      }
      q.busy = false;
    };
    return pump();
  }

  const stamp = (body) => ({ ...body, updatedAt: new Date().toISOString() });
  const get = (collection, id) => cache[collection][id];

  function exportAll() {
    return JSON.stringify({ exportedAt: new Date().toISOString(), ...cache }, null, 1);
  }

  return {
    init, onChange, get, exportAll,
    get mode() { return mode; },
    get readOnly() { return readOnly; },
    all: (collection) => cache[collection],
    saveGate: (id, body) => write("gates", id, stamp(body)),
    saveScale: (id, body) => write("scales", id, stamp(body)),
    saveComparison: (id, body) => write("comparisons", id, stamp(body)),
    saveEareps: (body) => write("eareps", "responses", stamp(body)),
  };
})();
