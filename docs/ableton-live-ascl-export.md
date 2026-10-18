# Exporting a Wilsonic tuning for Ableton Live (.ascl)

Ableton Live 12 can load a tuning system from an `.ascl` file, but Live has no
MTS-ESP support, so until now the only way to play a Wilsonic scale in Live was
to keep Wilsonic running as the MTS-ESP master and use plugins that listen to
it. I added an export so that a Live Set that has no MTS-ESP at all can still
play what I am exploring in the Wilsonic standalone. The file is a Scala `.scl`
body with Ableton's `! @ABL` directives in comment lines, so an ordinary Scala
reader still accepts it, and Live reads the directives to place the scale on the
keyboard and to label the piano roll.

## How to export

1. In Wilsonic, dial in the tuning you want: the design, its parameters, and
   the middle C note number, frequency and octave in the keyboard settings.
2. Click the MTS-ESP status light at the top right to open its menu, and
   choose **Export for Ableton Live (.ascl)…**. The export is desktop only, so
   it does not appear on iOS or Android.
3. Pick a file name. Wilsonic suggests one built from the design and its
   parameters, for example `CPS_4_2_A=1_B=3_C=5_D=7.ascl`.
4. If Wilsonic has something to tell you about the export (see the list of
   warnings below), it shows them after the file is written. The file is still
   written.

## How to load the file in Live

1. In Live 12, open the browser and go to **Tunings**, then use **Add
   Folder** to point Live at the folder where you saved the file, or drag the
   `.ascl` file into the browser's **User Library > Tunings** folder.
2. Drag the tuning onto the Set, or double-click it. Live then shows the tuning
   name at the bottom of the browser and plays every MIDI key 0 to 127 at the
   frequency Wilsonic's tuning table gave that key when you exported.
3. If the Set already has MIDI clips, Live offers to move their notes to the
   keys nearest their old pitches. That changes key numbers in your clips, so
   decline it if the clips were written for this tuning already. The export
   cannot control that dialog.

Live's own instruments (Operator, Wavetable, Drift, Analog, Collision, Tension,
Electric, Simpler and Sampler) read the tuning table directly. Third-party
plugins are tuned with per-note MPE pitch bend instead, so for those you need
to:

- turn on MPE for the plugin in its device title bar menu, and
- set the plugin's pitch bend range to **±48 semitones**, because that is the
  range Live assumes when it computes the bend values (one bend step is then
  about 0.586 cents).

If the synth cannot do ±48 semitones of bend, Live cannot reach the pitches,
and you will hear the scale compressed toward 12-tone equal temperament.

## What the export contains

- Every degree of the current scale after Wilsonic's own processing: period
  reduction, sort, uniquify and the notes-per-octave override are all applied
  first, so the file plays what you hear.
- Degree names in Live's piano roll. CPS scales carry their seed letters
  (`AB`, `AC`, `ABD`), MOS scales carry their scale degree with the tonic as
  `0`, equal temperaments read `3\12` the way Ableton's own EDO files do,
  rational scales (Diamonds, Partch, Euler genus, Scala imports and so on)
  carry their ratio such as `5/4`, and everything else carries its cents to
  one decimal such as `386.3¢`. When two degrees are merged by uniquify their
  names are joined with `|`, as in Ableton's `C♯|D♭`.
- The reference pitch and key range, so key 60 in Live is Wilsonic's middle C
  at the frequency you set, and keys 0 and 127 match too.
- Header comments with the export date, the design, the full parameter
  description, and one line per degree giving its name, value and cents.

## Things to know

**The export is a snapshot.** Nothing in the file updates when you move a
slider in Wilsonic. Export again and reload in Live when the tuning changes.

**Do not run both at once for the same synth.** If Wilsonic is still running
as the MTS-ESP master in the same Set, any MTS-ESP-aware synth will be tuned
twice: once by Wilsonic's tuning table and once by Live's pitch bend. The
result is the scale applied on top of itself. Either load the `.ascl` in Live
or run Wilsonic as master, and if you use the file, remove Wilsonic from the
Set or make sure the synths are not MTS-ESP clients.

**Warnings you may see after exporting.** The file is still written in every
case; these tell you where Live and Wilsonic will differ.

- *Keys outside 4 Hz to 21 kHz.* Live will not play them. A 6-note scale
  spans 21 periods across 128 keys, so many of its outer keys fall outside
  that window. This is normal for small scales and matches Wilsonic's own
  table.
- *Filtered notes.* Wilsonic can filter individual notes out of MTS-ESP, but
  the `.ascl` format has no way to express that, so Live plays every key.
- *12-note tuning, middle C not on a multiple of 12.* Live labels any 12-note
  tuning from key 0 by key mod 12, ignoring the scale's own degree assignment,
  so Wilsonic rotates the name list to compensate. The piano roll labels then
  land on the right keys, but Live's tuning list shows the names in rotated
  order. I have only seen this rule in Live's code, so please tell me if the
  labels come out wrong on your machine.
- *Degrees not ascending, duplicated, or outside the period.* These happen
  when sort or period reduction is off in Wilsonic. Live's handling of such a
  degree list is untested.
- *Octave labels shifted.* Live only allows octave numbers from -99 to 99. A
  1- or 2-note scale with middle C near either end of the keyboard needs more
  room than that, so middle C is labelled with an octave other than 3.

**What the export refuses.** An empty scale, a period of 1 or less, or a
degree with a non-positive or non-finite value cannot be written, and Wilsonic
says so instead of writing a file.
