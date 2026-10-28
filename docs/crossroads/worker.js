// Runs the gap-filling methods off the page's thread, one method family at a
// time, and posts each family's results as soon as they are ready.
"use strict";
importScripts("engine.js");

const FAMILIES = [
  ["PARENT-CS"],
  ["EPI-AM", "EPI-HM", "EPI-MED", "EPI-CS"],
  ["GENUS-GREEDY", "GENUS-CS"],
  ["MOS-GREEDY", "MOS-CS", "MOS-PURE"],
  ["REC-GREEDY", "REC-CS"],
];

self.onmessage = (e) => {
  const { job, tones, parent, genus, opts, methods } = e.data;
  for (const fam of FAMILIES) {
    const only = fam.filter((m) => methods.includes(m));
    if (!only.length) continue;
    try {
      const res = Engine.fillAll(tones, parent, genus, opts, only);
      self.postMessage({ job, res });
    } catch (err) {
      self.postMessage({ job, error: `${only.join(", ")}: ${err.message}` });
    }
  }
  self.postMessage({ job, done: true });
};
