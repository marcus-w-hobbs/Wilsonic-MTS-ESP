# MTS-ESP and Your DAW

This chapter is where Wilsonic becomes useful beyond its reference synth:
one instance of Wilsonic retunes every compatible synth in your session, in
real time, while you design the scale.

## What is MTS-ESP?

[MTS-ESP](https://github.com/ODDSound/MTS-ESP) is ODDSound's protocol for
sharing tuning data between plugins in a DAW, automatically and invisibly,
with no routing or setup. A few properties are worth understanding, because
they explain most of the behavior you will see:

- MTS-ESP does **not** use MIDI. Tuning data never passes through your
  DAW's MIDI connections; it is shared directly between plugins. Because
  the DAW is not involved at all, it works in any DAW.
- There is one **master** (Wilsonic) that publishes a global tuning table,
  and any number of **clients** (your synths) that follow it.
- Developers must explicitly add MTS-ESP support to a synth for this to
  work. ODDSound keeps a
  [list of supported plugins and DAW setup notes](https://oddsound.com/usingmtsesp.php).
- Most MTS-ESP synths retune to Wilsonic the moment they load. Some have a
  preference you must enable first — Surge XT, for example, has an MTS-ESP
  setting in its tuning menu.
- A synth's MPE support alone does not mean it supports MTS-ESP. They are
  different things, though MPE helps with the fallback described below.

## Setup

1. Load **Wilsonic** (AU or VST3) on a MIDI track. Keep it the only
   MTS-ESP master in the session, and check the
   [status indicator](installation.md#the-mts-esp-status-indicator) is
   green.
2. Load MTS-ESP-aware synths on other tracks. They follow Wilsonic's
   tuning automatically.
3. Play the Wilsonic track's MIDI into the simple synth and A/B it against
   your other synths to confirm everything agrees.

Your software synths are the clients; Wilsonic publishes the global tuning
table they all read.

## Synths that do not support MTS-ESP

Synths without native MTS-ESP support can usually still be retuned using
MIDI pitch-bend messages, and this even works polyphonically for synths
that support MPE. The pitch-bend route needs a translator plugin that reads
the MTS-ESP tuning table and emits pitch-bend in response:

- **Paid:** [ODDSound MTS-ESP MIDI Client](https://oddsound.com/dl/ODDSound_MTS_ESP_Suite_MIDI_Client_Manual.pdf),
  part of the MTS-ESP Suite.
- **Free:** the Ableton Microtuner M4L device (in MTS-ESP client mode), and
  Xen MIDI Retuner.

## Videos

I find these walkthroughs the fastest way to see a working setup:

- [How to install ODDSound plug-ins on Mac and Windows](https://youtu.be/G97IyCI3za0)
- [Microtuning in Ableton Live with MTS-ESP](https://youtu.be/sUGQeh3ViFM)
- [Microtuning in Bitwig Studio with MTS-ESP](https://youtu.be/XOcK2PvytuM)
