# Troubleshooting

These are the questions I actually get, so if yours is not here, please ask
it on [GitHub Issues](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/issues)
and I will answer it and add it.

## The app makes no sound

This is the most common question, and the answer is almost always one of
these, in order of likelihood:

1. **You opened WilsonicController.** It is a MIDI effect and makes no
   sound by itself, by design. Open **Wilsonic**, the app *without*
   "Controller" in the name — it has a built-in simple synth. The
   difference is explained in [Which Wilsonic Is Which](which-wilsonic.md).
2. **No audio output is selected.** In standalone Wilsonic, open
   **Options → Audio/MIDI Settings** and check the output device.
3. **Nothing is playing the synth.** Click the microtonal keyboard at the
   bottom of the window with the mouse. A connected MIDI keyboard must be
   enabled as a MIDI input in **Options → Audio/MIDI Settings** before it
   will play the simple synth.

And remember the simple synth is a reference instrument. The intended
sound of Wilsonic is your own synths, retuned over MTS-ESP in a DAW, which
is covered in [MTS-ESP and Your DAW](daw-setup.md).

## The status indicator is yellow

Yellow means this instance is not managing the global tuning table —
usually another MTS-ESP master is already running, or a crash left a stale
registration. Close other instances of Wilsonic, WilsonicController, and
any other MTS-ESP master plugin, then choose **Register** from the menu.
See [the status indicator](installation.md#the-mts-esp-status-indicator).

## My synth does not retune

- Check the synth actually supports MTS-ESP on
  [ODDSound's supported-plugins list](https://oddsound.com/usingmtsesp.php).
  MPE support alone does not establish MTS-ESP support.
- Some synths support MTS-ESP but ship with it disabled. Surge XT, for
  example, has an MTS-ESP preference in its tuning menu.
- Check Wilsonic's status indicator is green — only the active master
  retunes clients.
- Synths without MTS-ESP support can usually be retuned over MIDI
  pitch-bend; the options are listed in
  [MTS-ESP and Your DAW](daw-setup.md#synths-that-do-not-support-mts-esp).

## Can I run Wilsonic and WilsonicController at the same time?

Please don't, for now. Each wants to be the MTS-ESP master, and I have not
yet built graceful hand-off between two masters, so the tuning state gets
confusing. Run one or the other.

## The plugin does not show up in my DAW

- Rescan plugins in your DAW's preferences.
- On macOS the release includes AU and VST3; on Windows it includes VST3.
  Check your host actually loads that format.
- Reboot after installing if you have not — the MTS-ESP library is loaded
  system-wide.

## Something else is wrong

Open an issue on
[GitHub Issues](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/issues)
and include the version you installed, your operating system, your DAW or
host if any, and the steps that reproduce the problem. Issues are public,
so keep private information out. For tuning-research conversation rather
than support, I use
[GitHub Discussions](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/discussions).
