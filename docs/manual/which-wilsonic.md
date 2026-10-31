# Which Wilsonic Is Which

I ship two desktop targets from one codebase, and I also made a separate iOS
app years earlier, so there are three things in the world called "Wilsonic."
This page exists because the difference is the single most common source of
confusion I hear about, usually in the form of "the app makes no sound."

## The short version

| | Makes sound by itself | MTS-ESP source | Sends MIDI | Formats |
|---|---|---|---|---|
| **Wilsonic** | **Yes** — built-in simple synth | Yes | No | Standalone, AU, VST3 |
| **WilsonicController** | **No** — silent by design | Yes | Yes | Standalone, AU, VST3 |
| **Wilsonic for iOS** | Yes | No | No | Separate [App Store app](https://apps.apple.com/us/app/wilsonic/id848852071) |

## Wilsonic

Wilsonic is the one to start with. It is an MTS-ESP source — it broadcasts
the global tuning table that your other synths follow — and it has a simple
built-in synth so you can hear scales on their own and confirm your other
synths are in tune. As a standalone app, clicking the microtonal keyboard
makes sound immediately. As a plugin on a MIDI track, the track's MIDI plays
the simple synth, and the scale-design parameters are automatable in your
DAW.

## WilsonicController

WilsonicController is the same scale-design interface, but built as a MIDI
effect. It is both an MTS-ESP source and a MIDI source, and it has **no
synth at all**. I built it so you can perform on Erv Wilson's generalized
keyboard layouts — the Gral keyboards, the CoPrime grid, the Partch
diamonds — and send that performance as MIDI into any instrument, while the
tuning table retunes every MTS-ESP synth at the same time. If you opened
WilsonicController and heard nothing, nothing is broken; it needs an
instrument downstream to make sound.

One important caution: run only one of them at a time. Each wants to be the
MTS-ESP master, and I have not yet built graceful hand-off between two
masters, so running both at once leads to confusing tuning states. See
[the status indicator](installation.md#the-mts-esp-status-indicator) for how
to tell who is master.

## Wilsonic for iOS

Wilsonic for iOS is an older, separate app for exploring and playing scale
designs on a touchscreen. It does not participate in MTS-ESP and is not a
plugin. The [App Store listing](https://apps.apple.com/us/app/wilsonic/id848852071)
has current device requirements and availability.
