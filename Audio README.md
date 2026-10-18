How it works now
One audio device: the class opens a single miniaudio output and mixes up to 20 sound channels plus a music channel itself. The pyminiaudio source confirms the device accepts the NumPy blocks this mixer sends.

No helper threads: sounds start immediately, and fades, loops, maxtime and queues are timed inside the audio stream. Your ThreadClass import is gone.

Music doesn't freeze the GUI: it's decoded on a background thread. Starting a new track before the previous one finishes loading cancels the older request.

No audio device: the game logs it and keeps running silently instead of crashing.

Things to know
File formats: WAV, MP3, FLAC and OGG only. AIFF and MP4 files will need converting.

Memory: files are fully decoded into memory, roughly 30 MB for a 3-minute track, and freed when you change themes.

New default: playMusic now plays once by default (loops=0). Your old default of loops=1 played the track twice in pygame.

Bug fixes:

currentMusic was never set before use.

mute, unmute and unpauseAllSounds all just paused.

addSound kept adding extensions onto the same filename.

quit() called stopSound() with no name, which raised an error.

chooseTheme crashed when switching themes.

The .delete() calls on dicts don't exist.

The music filename and display name were swapped in soundtracks.

Startup music never started.

Packaging: if you build with PyInstaller for macOS, you may need --collect-all miniaudio so its compiled library is included.

Files are in my workspace:

SoundMixerClass.py


SoundMixerClass.py (just_playback version)
Python
Run the miniaudio version against my actual game files
Add PyInstaller packaging support for miniaudio
Review the replacement for any remaining compatibility issues

dnswire: Library for encoding/decoding different DNS encapsulations
planetiler: Flexible tool to build planet-scale vector tilesets from OpenStreetMap data fast
portop: Terminal UI showing which processes are using TCP and UDP ports
tinyframe: Minimalistic library for reading and writing the Frame Streams protocol
titus: High-performance secrets scanner

You have 4 outdated formulae installed.

==> Downloading bottle manifests
✔︎ Bottle Manifest miniaudio (0.11.25)                                                                    Downloaded   10.0KB/ 10.0KB
✔︎ Bottle Manifest numpy (2.5.4)                                                                          Downloaded   76.4KB/ 76.4KB
==> Would install 2 formulae:
miniaudio  0.11.25
numpy      2.5.4
==> Would install 7 dependencies for numpy:
gmp
isl
mpfr
libmpc
gcc
libomp
openblas
