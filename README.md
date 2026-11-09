# Build a standalone Last King app on your Mac

These steps are for macOS only.

The game code and assets are not in this repository. Clone them from https://github.com/Professor-Jeffry-Yeates/Last-King-Project-11.0. You install Python 3.14, compile pygame for that interpreter, then point a packager at that clone, at `ClassIntro.py`, and at an `.icns` made from `LastKing_ico.png`. After you change the game, you run the packager again by hand. Nothing here is built on GitHub. A Windows 11 build is out of scope.

Use the Python 3.14 from python.org, not the `python3` that ships with macOS at `/usr/bin/python3`. That file is Apple's and is the wrong interpreter for this build.

## 1. Install Python 3.14.8

Python 3.14.8 is the current 3.14 release (30 September 2026). The macOS installer is a universal2 package for macOS 10.15 and later:

https://www.python.org/downloads/release/python-3148/

https://www.python.org/ftp/python/3.14.8/python-3.14.8-macos11.pkg

Either open that `.pkg` in Installer, or from Terminal:

```bash
curl -L -O https://www.python.org/ftp/python/3.14.8/python-3.14.8-macos11.pkg
sudo installer -pkg python-3.14.8-macos11.pkg -target /
```

On the Installation Type step, click Customize. If a free-threaded Python package is listed, leave it unchecked. [py2app 0.28.9](https://github.com/ronaldoussoren/py2app/releases/tag/v0.28.9) does not support free-threaded Python, and 0.28.10 does not add that support.

When the installer finishes, run the certificate helper it just installed:

```bash
"/Applications/Python 3.14/Install Certificates.command"
```

Check that you have the normal 3.14 build, not the free-threaded one:

```bash
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -VV
```

The line must start with `Python 3.14.8` and must not say `free-threading build`. The rest of this page calls that binary `python3.14`. If `/usr/local/bin` is on your `PATH`, `python3.14` is the same program. Do not use `python3.14t`.

## 2. Compiler: what Python 3.14 actually requires

Install the current Xcode Command Line Tools. That provides `clang` at `/usr/bin/clang`:

```bash
xcode-select --install
clang --version
```

Python 3.14's public headers (`Python.h`) are compatible with C11 and C++11. That is a lower limit: the C API does not require a later standard, and you do not need to turn on the compiler's "c11 mode". This is the current text in the [Python 3.14 C API introduction](https://docs.python.org/3.14/c-api/intro.html), and it matches the C API working group's decision in [Python 3.14 headers will require C11 and C++11](https://discuss.python.org/t/python-3-14-headers-will-require-c11-and-c-11/79481).

pygame 2.6.1 does not set `-std=c++11`, or any other `-std=` flag, in its `setup.py`. Its extensions are C, with Objective-C on macOS. No pygame release note, install document, or issue names an older Xcode, an older Command Line Tools package, or a `-std=` flag as the way to build pygame for Python 3.14.

Do not export `CFLAGS` or `CXXFLAGS` for this build, and do not pass `-std=c++98`, `-std=c99`, `-std=c11`, or `-std=c++11`. Leave Apple clang on its default language mode.

Two different failures get talked about as a "wrong C++ standard". Only the first one is a language-mode error. The second is the failure a pygame 2.6.1 source build on Python 3.14 actually records on a Mac when the SDL headers are missing.

**Wrong language mode.** If a C++ compile is handed the C flag `-std=c11`, clang stops immediately with:

```text
error: invalid argument '-std=c11' not allowed with 'C++'
```

That is clang rejecting a C standard on a C++ (or Objective-C++) compile. It happens when `CFLAGS` from a C11 build of Python is reused as C++ flags. pygame 2.6.1's own build compiles `.c` files with `clang`, not `clang++`, and its issue tracker does not show this line for an unmodified Python 3.14 build. If you do see it, unset `CFLAGS` and `CXXFLAGS` and run the pygame install again. Do not "fix" it by switching to an older Command Line Tools.

Forcing a dialect older than the C11 / C++11 floor (`-std=c99` or `-std=c++98`) puts the compile outside the range Python 3.14 supports. The headers have used an anonymous union since Python 3.13. There is no pygame issue that quotes the diagnostic for that mistake, so this page does not invent one. Do not pass those flags.

**The macOS failure pygame does record on Python 3.14** is a missing SDL header, not a C++ standard. On an M4 Mac, building pygame 2.6.1 for Python 3.14 failed with ([pygame#4627](https://github.com/pygame/pygame/issues/4627)):

```text
src_c/_sdl2/sdl2.c:1237:10: fatal error: 'SDL.h' file not found
error: command '/usr/bin/clang' failed with exit code 1
```

The same missing header is [pygame#4476](https://github.com/pygame/pygame/issues/4476). Section 3 is what prevents it. There is still no cp314 wheel on PyPI: pygame 2.6.1's files stop at cp313, so `pip` builds the source tarball `pygame-2.6.1.tar.gz`.

One more failure that is not a compiler standard: pygame 2.6.1 wraps `distutils` `spawn` and passes `dry_run` only when `PYGAME_DETECT_AVX2` is set in the environment. setuptools 82 removed that attribute. The build then dies with ([pygame#4848](https://github.com/pygame/pygame/issues/4848)):

```text
AttributeError: 'Compiler' object has no attribute 'dry_run'
```

Do not set `PYGAME_DETECT_AVX2` for this Mac build. Unset it if it is already exported (`unset PYGAME_DETECT_AVX2`). Apple Silicon does not use those blitters. On an Intel Mac the build still succeeds without them.

## 3. Install the SDL libraries pygame looks for

pygame 2.6.1's `buildconfig/config_darwin.py` looks for `sdl2-config`, `SDL_ttf.h` / `libSDL2_ttf.dylib`, `SDL_image.h` / `libSDL2_image.dylib`, `SDL_mixer.h` / `libSDL2_mixer.dylib`, and `portmidi.h` / `libportmidi.dylib` under `/opt/homebrew` (Apple Silicon Homebrew) or `/usr/local` (Intel Homebrew). Freetype is found with `pkg-config freetype2`.

Install Homebrew from https://brew.sh if `brew` is not already on the machine. Then:

```bash
brew install pkgconf sdl2-compat sdl2_image sdl2_mixer sdl2_ttf portmidi
```

Homebrew's current `sdl2-compat` package is also known as `sdl2` and is the formula that ships `sdl2-config`. The old standalone `sdl2` formula page is gone. `sdl2_image`, `sdl2_mixer`, and `sdl2_ttf` depend on `sdl2-compat` (an SDL2 API in front of SDL3). `pkgconf` provides the `pkg-config` command. `sdl2_ttf` pulls in freetype, which is the library pygame's font check wants.

Confirm the files pygame searches for are visible:

```bash
sdl2-config --version
pkg-config --modversion freetype2
ls "$(brew --prefix)/include/SDL2/SDL.h" \
   "$(brew --prefix)/lib/libSDL2_image.dylib" \
   "$(brew --prefix)/lib/libSDL2_mixer.dylib" \
   "$(brew --prefix)/lib/libSDL2_ttf.dylib" \
   "$(brew --prefix)/lib/libportmidi.dylib"
```

`sdl2-config --version` must print a 2.x version. If Homebrew reports a conflict, keep the install that still provides those five paths. This page has not been verified by compiling pygame 2.6.1 against the SDL3-backed `sdl2-compat` layer. The header and library names match what `config_darwin.py` searches for. A later error inside an SDL call is not the C++ problem from section 2.

## 4. Build pygame 2.6.1 for this Python

Use a virtual environment created by that same `python3.14`, so the compile cannot pick up another interpreter. Put it outside the game folder.

```bash
unset CFLAGS CXXFLAGS PYGAME_DETECT_AVX2
python3.14 -m venv "$HOME/last-king-py314"
source "$HOME/last-king-py314/bin/activate"
python -m pip install --upgrade pip
python -m pip install --no-binary=pygame pygame==2.6.1
```

`--no-binary=pygame` forces a source build. Do not install Cython first. The 2.6.1 tarball already contains the generated C, and the build prints `Skipping Cython compilation` when Cython is absent.

Check the import with this interpreter:

```bash
python -c "import pygame; print(pygame.version.ver); print(pygame.version.SDL); print(pygame.__file__)"
```

`pygame.version.ver` must be `2.6.1`. `pygame.__file__` must sit under `$HOME/last-king-py314`. If the import fails before any game code runs, stop and fix this step. The packager can only bundle a pygame that this interpreter can import.

The clone does not pin another pygame. `SetupGameClass.py` imports `SoundMixerClass`, and `SoundMixerClass.py` still does `import pygame` and uses `pygame.mixer`. `MiniAudioSoundMixerClass.py` is in the same folder, but the whole file is comments, including `import miniaudio`, and no module imports it. This build stays on pygame 2.6.1. Do not install miniaudio for it.

## 5. Pack the app, using LastKing_ico.png

The packager is py2app 0.28.10, the current release on PyPI. Python 3.14 support was added in 0.28.9. 0.28.10 is the same support plus a fix for setuptools 82 ([py2app 0.28.10](https://github.com/ronaldoussoren/py2app/releases/tag/v0.28.10)). The [Python macOS documentation](https://docs.python.org/3/using/mac.html) lists py2app as the tool that builds a macOS `.app`.

```bash
python -m pip install py2app==0.28.10
```

Stay in the same virtual environment. Create a build directory that is not inside the game folder and not inside this repository:

```bash
mkdir -p "$HOME/last-king-mac-build"
cd "$HOME/last-king-mac-build"
```

Clone the game outside this repository and outside the build directory. Set three paths from that clone:

- `GAME_DIR` is the clone of https://github.com/Professor-Jeffry-Yeates/Last-King-Project-11.0.
- `ENTRY` is `ClassIntro.py` at the root of that clone. py2app names the `.app` after that file, so the bundle is `dist/ClassIntro.app`. The [py2app tutorial](https://py2app.readthedocs.io/en/latest/tutorial.html) shows the same naming with its own example: `MyApplication.py` becomes `dist/MyApplication.app`.
- `ICON` is an `.icns` made from `LastKing_ico.png`, also at the root of the clone. That file is a PNG, not an `.iconset`. py2app's `iconfile` option wants an `.icns`. Build the iconset with `sips`, then run `iconutil -c icns` on it.

```bash
git clone https://github.com/Professor-Jeffry-Yeates/Last-King-Project-11.0.git "$HOME/Last-King-Project-11.0"
GAME_DIR="$HOME/Last-King-Project-11.0"
ENTRY="$GAME_DIR/ClassIntro.py"
PNG="$GAME_DIR/LastKing_ico.png"
ICONSET="$HOME/last-king-mac-build/LastKing.iconset"
mkdir -p "$ICONSET"
sips -z 16 16     "$PNG" --out "$ICONSET/icon_16x16.png"
sips -z 32 32     "$PNG" --out "$ICONSET/icon_16x16@2x.png"
sips -z 32 32     "$PNG" --out "$ICONSET/icon_32x32.png"
sips -z 64 64     "$PNG" --out "$ICONSET/icon_32x32@2x.png"
sips -z 128 128   "$PNG" --out "$ICONSET/icon_128x128.png"
sips -z 256 256   "$PNG" --out "$ICONSET/icon_128x128@2x.png"
sips -z 256 256   "$PNG" --out "$ICONSET/icon_256x256.png"
sips -z 512 512   "$PNG" --out "$ICONSET/icon_256x256@2x.png"
sips -z 512 512   "$PNG" --out "$ICONSET/icon_512x512.png"
sips -z 1024 1024 "$PNG" --out "$ICONSET/icon_512x512@2x.png"
iconutil -c icns -o "$HOME/last-king-mac-build/LastKing.icns" "$ICONSET"
ICON="$HOME/last-king-mac-build/LastKing.icns"
```

`ClassIntro.py` starts the game from the modules that sit next to it, and it opens the folder `Quiz_Content` by that name. The window is Tk. `CoffeeCanvas.py` imports `tkinter` and creates `tk.Tk()`. Leave tkinter in the bundle. `SoundMixerClass.py` imports pygame for sound, which is why section 4 builds pygame 2.6.1. On macOS, `QuizClass.py` imports `Mac_PlatformSpecific.py`, which imports `appscript` and `mactypes`. `CoffeeCanvas.py` imports Pillow (`PIL`) when it is installed; map and picture loads use that. `appscript` and Pillow are not files in the clone. Install them in this same virtual environment so the packager can see them:

```bash
python -m pip install appscript Pillow
```

The copy step below still has to include the files that live next to `ClassIntro.py`. The important ones are the other `.py` modules in the clone root (they are imported by file name, not as a package) and the `Quiz_Content` directory. That includes `MiniAudioSoundMixerClass.py`, which is copied because it sits next to the entry even though nothing imports it. `Quiz_Content` holds `Instructions.json`, `Questions.json`, `Places.json`, `GameObjects.json`, `Objects.json`, `ScenarioObjects.json`, and the `Maps`, `Music`, `Sounds`, `Objects`, `Problems`, `Problems - Key`, and `Vocabulary` folders. `LastKing_ico.png` and `No Picture Warning.png` are also at the clone root. Do not copy the game source into this repository.

Write `setup.py` in the build directory from the clone. `app` is `ClassIntro.py`. `iconfile` is the `.icns` from above. `packages` includes pygame, so the extensions compiled in section 4 are copied whole, and it includes `PIL`, `appscript`, and `mactypes` so those imports are copied too.

py2app starts the app with the working directory set to `Contents/Resources`, and each `resources` path is copied there under its own name. Copying `GAME_DIR` as a single resource would nest files one level down (`Contents/Resources/<folder name>/...`), so a relative open such as a file next to the script would miss. The command below lists each file and directory that is already directly inside `GAME_DIR`, skips the entry script, and skips hidden names and `__pycache__`.

```bash
export GAME_DIR ENTRY ICON
python <<'PY'
import os
from pathlib import Path

game = Path(os.environ["GAME_DIR"])
entry = Path(os.environ["ENTRY"]).resolve()
icon = os.environ["ICON"]
resources = []
for child in sorted(game.iterdir()):
    if child.name.startswith(".") or child.name == "__pycache__":
        continue
    if child.resolve() == entry:
        continue
    resources.append(child)

lines = [
    "import py2app.build_app as py2app_build_app",
    "",
    "# py2app 0.28.10 already skips libtclstub8.6.a and libtkstub8.6.a.",
    "# Python 3.14.8 ships Tcl/Tk 9.0.3, which names those archives",
    "# libtclstub.a and libtkstub.a. Leave them out of the copy.",
    "for _stub_name in ('libtclstub.a', 'libtkstub.a'):",
    "    if _stub_name not in py2app_build_app._IGNORE_FILES:",
    "        py2app_build_app._IGNORE_FILES.append(_stub_name)",
    "",
    "from setuptools import setup",
    "",
    "setup(",
    f"    app=[{str(entry)!r}],",
    "    options={",
    '        "py2app": {',
    f"            \"iconfile\": {icon!r},",
    '            "packages": ["pygame", "PIL", "appscript", "mactypes"],',
    '            "resources": [',
]
for path in resources:
    lines.append(f"                {str(path)!r},")
lines += [
    "            ],",
    "        }",
    "    },",
    ")",
    "",
]
Path("setup.py").write_text("\n".join(lines))
print("entry:", entry)
print("icon:", icon)
print("resources:")
for path in resources:
    print(" ", path)
PY
```

Read the printed resource list before you build. If the game loads a file that lives outside `GAME_DIR`, add that path to the `resources` list in `setup.py`. Do not add `--alias` or `--semi-standalone`. Both of those still need a Python installation outside the app ([py2app options](https://py2app.readthedocs.io/en/latest/options.html)). Do not pass `--argv-emulation`; the py2app docs say that option confuses GUI toolkits.

## The Tcl 9 stub archive

A finished `python setup.py py2app` run signs the bundle itself. The signer is `codesign -s - --preserve-metadata=identifier,entitlements,flags,runtime -f -vvvv`, which is `codesign_adhoc` in [py2app 0.28.10 `util.py`](https://github.com/ronaldoussoren/py2app/blob/v0.28.10/py2app/util.py). When that walk reaches a static archive inside a framework, codesign stops and names the file. [Technical Note TN2206](https://developer.apple.com/library/archive/technotes/tn2206/_index.html) says the `In subcomponent:` line is the nested item that failed. On this build the line is:

```text
In subcomponent: .../ClassIntro.app/Contents/Frameworks/Tcl.framework/Versions/9.0/libtclstub.a
```

py2app then raises `RuntimeError: Cannot sign bundle`. The same codesign command, run again on a bundle that still contains `libtclstub.a`, stops on that same line. Signing is not a separate repair step.

Python 3.14.8's macOS installer includes Tcl/Tk 9.0.3 ([python.org discussion](https://discuss.python.org/t/python-org-macos-installer-users-of-tkinter-python-3-14-with-tcl-tk-9-0-3-instead-of-8-6-17/107206), [CPython gh-124111](https://github.com/python/cpython/issues/149463)). Tcl 9 names the link-time stub archive `libtclstub.a`, and Tk 9 names its pair `libtkstub.a` ([TIP 628](https://core.tcl-lang.org/tips/doc/main/tip/628.md)). py2app 0.28.10 already refuses to copy the Tcl 8.6 names `libtclstub8.6.a` and `libtkstub8.6.a`, plus `tclConfig.sh`, `tkConfig.sh`, and `tclooConfig.sh`, because those files make this sign step fail on the python.org 3.13 and 3.14 installers. That list is `_IGNORE_FILES` in [`build_app.py`](https://github.com/ronaldoussoren/py2app/blob/v0.28.10/py2app/build_app.py), applied by `framework_copy_condition`. The 9.0 names are not in the list, so they are copied into `Versions/9.0/` and codesign stops.

Keep Tk in the app. `ClassIntro.py` reaches `CoffeeCanvas.py`, which imports `tkinter` and opens the window with `tk.Tk()`. The shared libraries `Tcl.framework/Versions/9.0/Tcl` and `Tk.framework/Versions/9.0/Tk` are what that window loads. The `.a` files are the stub archives a C extension links against at build time. They are not needed in the finished app. The `setup.py` writer above appends `libtclstub.a` and `libtkstub.a` to `_IGNORE_FILES` before `setup()` runs, which is the same filter py2app already uses for the 8.6 archives. `framework_copy_condition` then skips both files, and py2app's own sign step can finish.

Write `setup.py` with the command above, then build from an empty output directory. An earlier `dist/ClassIntro.app` that stopped on `libtclstub.a` is removed by the `rm`:

```bash
rm -rf build dist
python setup.py py2app --iconfile "$ICON"
```

The build is past `libtclstub.a` when that command exits 0 and this prints no paths:

```bash
APP="$HOME/last-king-mac-build/dist/ClassIntro.app"
find "$APP" \( -name 'libtclstub.a' -o -name 'libtkstub.a' \) -print
```

The frameworks themselves stay in the bundle:

```bash
ls -d "$APP/Contents/Frameworks/Tcl.framework/Versions/9.0" \
      "$APP/Contents/Frameworks/Tk.framework/Versions/9.0"
```

`dist/ClassIntro.app` is the app. Finder hides the `.app` suffix. Launch it with the command in section 7. The last directory on that `PATH` is `/sbin`.

## 6. Rebuild after you change the game

A standalone bundle does not watch your source tree. After you edit code or assets, clean the previous output and run py2app again from the same environment:

```bash
source "$HOME/last-king-py314/bin/activate"
cd "$HOME/last-king-mac-build"
rm -rf build dist
python setup.py py2app --iconfile "$ICON"
```

You do not repeat sections 1–4 unless you deleted the virtual environment or upgraded Python. You do not rebuild pygame unless you recreated that environment. If you added or removed a file directly under `GAME_DIR`, run the `setup.py` writer in section 5 again so `resources` matches the folder, then run the commands above. Editing a file that is already listed does not require a new `setup.py`. A bundle that already failed on `libtclstub.a` does: run that writer again so `libtclstub.a` and `libtkstub.a` are on `_IGNORE_FILES`, then run the commands above.

## 7. Confirm the app runs without a system Python

The default `py2app` command (no `--alias`, no `--semi-standalone`) is the self-contained build. Check that Python was copied into the bundle. This directory is missing when the build still depends on an outside interpreter:

```bash
APP="$(find "$HOME/last-king-mac-build/dist" -maxdepth 1 -name '*.app' -print -quit)"
ls -d "$APP/Contents/Frameworks/Python.framework/Versions/3.14"
file "$APP/Contents/MacOS/"*
```

`file` should describe a Mach-O executable, not a script whose first line is `/usr/bin/python3`.

Launch that executable with a `PATH` that does not include `/usr/local/bin` or the python.org framework `bin` directory. The last directory is `/sbin`:

```bash
env -i \
  PATH="/usr/bin:/bin:/usr/sbin:/sbin" \
  HOME="$HOME" \
  TMPDIR="${TMPDIR:-/tmp}" \
  "$APP/Contents/MacOS/$(basename "$APP" .app)"
```

The game window should open. `/usr/bin/python3` is still on that `PATH`; it is Apple's interpreter, and the Mach-O under `Contents/MacOS` is not it. The interpreter in use is the framework copy under `Contents/Frameworks`.

Also confirm the SDL libraries were copied into the bundle, so the app is not still loading Homebrew at runtime:

```bash
find "$APP" \( -name 'libSDL2*.dylib' -o -name 'SDL2' -o -name 'libSDL2*' \) -print
```

py2app rewrites non-system shared libraries into the bundle. If that `find` prints nothing, the app still needs the Homebrew SDL from section 3 even though it no longer needs `python3.14` on `PATH`.

You can also double-click the `.app` in Finder, or run `open "$APP"`. A local build is not quarantined the way a downloaded zip is. Output from a Finder launch goes to Console.app (`open -a Console`), which is the py2app tutorial's note for a normal launch.
'''
SDL-3 did not load. A quick fix:
brew install sdl3
APP="$HOME/last-king-mac-build/dist/ClassIntro.app"
find "$APP" \( -name 'libtclstub.a' -o -name 'libtkstub.a' \) -print
cp -L "$(brew --prefix sdl3)/lib/libSDL3.dylib" "$APP/Contents/Frameworks/libSDL3.dylib"
install_name_tool -id "@loader_path/libSDL3.dylib" "$APP/Contents/Frameworks/libSDL3.dylib"
otool -L "$APP/Contents/Frameworks/libSDL3.dylib"
codesign -s - -f "$APP/Contents/Frameworks/libSDL3.dylib"
codesign -s - -f --preserve-metadata=identifier,entitlements,flags,runtime "$APP"
'''
Now run
'''
env -i \
  PATH="/usr/bin:/bin:/usr/sbin:/sbin" \
  HOME="$HOME" \
  TMPDIR="${TMPDIR:-/tmp}" \
  "$APP/Contents/MacOS/$(basename "$APP" .app)"
  '''