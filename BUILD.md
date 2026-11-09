<<<<<<< HEAD
# Building Student Python Review as a Windows executable

These steps create a standalone `.exe` so students do not need Python installed.

## Prerequisites

- Windows
- Python 3 installed and on your PATH (`python --version` works in a terminal)
- This project folder, including the `Problems` folder

## First-time build

1. Open a terminal in this project folder  
   (`...\CIS-130 Python - FA26\Python Review - Student`).
2. Run:

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1 -OneFile
```

3. Find the result:

| Mode | Command | Output |
|------|---------|--------|
| One-file (recommended for students) | `build.ps1 -OneFile` | `dist\StudentPythonReview.exe` |
| Folder distribution | `build.ps1` | `dist\StudentPythonReview\StudentPythonReview.exe` |

One-file: give students only `StudentPythonReview.exe` (problem files are packed inside).  
Folder build: copy the **entire** `dist\StudentPythonReview` folder.

## Rebuild after you change the app

Do this whenever you change code or problem content and want a new `.exe`.

1. Edit the source as needed, for example:
   - `CodeReview.py` (main program)
   - `CoffeeBean.py`, `CoffeeCanvas.py`, `CoffeeColors.py`, `SafeNodeVisitorClass.py`
   - files under `Problems\`
2. Rebuild (skip reinstalling packages if they are already installed):

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1 -OneFile -SkipInstall
```

3. Replace the old copy of the executable (or folder) with the new one from `dist\`.

## What gets packaged

- Entry point: `CodeReview.py`
- Local modules: `SafeNodeVisitorClass`, `CoffeeBean`, `CoffeeCanvas`, `CoffeeColors`
- Data: entire `Problems` folder
- Runtime helpers: `tkinter`, `Pillow` (PIL)

You do **not** need to include helper/test files such as `CodeTestOne.py` or `Helpful Text Answers.py` unless you start importing them from the app.

## Optional: change the executable name or options

Edit the matching `.spec` file, then rebuild:

| Build type | Spec file |
|------------|-----------|
| Folder | `StudentPythonReview.spec` |
| One-file | `StudentPythonReview-onefile.spec` |

Useful fields: `name='StudentPythonReview'`, `console=False` (no console window), and `datas=[('Problems', 'Problems')]`.

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1 -OneFile -SkipInstall
```

## Note about the editor warning near `myFunction`

Around the `answer = myFunction(*parameters)` line in `CodeReview.py`, the editor may warn that `myFunction` is undefined. That is expected: the function is created at runtime by `exec(...)`. The warning is safe to ignore.

## Troubleshooting

- **"Problems folder not found" at build time**  
  Make sure you run `build.ps1` from this project folder and that `Problems\` exists.

- **Exe starts but shows no problems**  
  Rebuild so `Problems` is included. Path lookup uses `app_base_dir()` in `CodeReview.py` for both normal Python and frozen `.exe` runs.

- **Antivirus blocks the new exe**  
  Common with PyInstaller. Unblock via Windows security / allow the file, or rebuild and redistribute.

- **Need packages reinstalled**  
  Omit `-SkipInstall` so the script upgrades `pyinstaller` and `pillow`.
=======
# Student Python Review — macOS Build & Modification Guide

This project now targets **macOS** as a standalone `.app`. It was originally built
for Windows only — see `BUILD_WINDOWS.md` for the old `.exe` steps, which still
work if you ever need to build for Windows again.

The Python code itself (`CodeReview.py`, `CoffeeBean.py`, `CoffeeCanvas.py`,
`CoffeeColors.py`, `SafeNodeVisitorClass.py`) was already cross-platform —
it uses only `tkinter`, `Pillow`, and the standard library, and already detects
macOS vs. Windows at runtime (see "How the code adapts to macOS" below). The
things that were Windows-only were the **build tooling**: `build.ps1`
(PowerShell) and the `.exe`/`build\` artifacts. Those have been replaced with
macOS equivalents described below.

---

## Option A — Build automatically on GitHub (recommended, no Mac required)

Because PyInstaller must run on the same OS it's building for, a genuine macOS
`.app` has to be produced on real Apple hardware. This repo includes a GitHub
Actions workflow, `.github/workflows/build-macos.yml`, that does this for you
on GitHub's own macOS runners — you don't need your own Mac at all.

1. Push this repo to GitHub (already done if you're reading this from the repo).
2. Go to the repo on GitHub → **Actions** tab → **Build macOS App** → **Run workflow**.
3. Wait ~3-8 minutes for the run to finish (green checkmark).
4. Open the completed run → scroll to **Artifacts** → download
   `StudentPythonReview-macOS.zip`.
5. Unzip it. Inside is `StudentPythonReview.app` — this is what you hand out
   to students (see "Distributing to students" below).

The workflow also runs automatically on every push to `main` that touches the
Python source, a `.spec` file, or the `Problems` folder, so you always have an
up-to-date build available.

### Optional: sign & notarize with your Apple Developer account

Without extra setup, the workflow ad-hoc signs the app, which works but shows
a Gatekeeper warning the first time a student opens it (easily bypassed — see
below). Since you have an Apple Developer account, you can eliminate that
warning entirely by adding these **repository secrets**
(GitHub repo → Settings → Secrets and variables → Actions → New repository secret):

| Secret name | Value |
|---|---|
| `APPLE_CERTIFICATE_P12` | Base64 of your exported "Developer ID Application" certificate (see steps below) |
| `APPLE_CERTIFICATE_PASSWORD` | The password you set when exporting the `.p12` |
| `APPLE_SIGNING_IDENTITY` | e.g. `Developer ID Application: Your Name (ABCDE12345)` |
| `APPLE_ID` | Your Apple ID email address |
| `APPLE_TEAM_ID` | Your 10-character Team ID (Apple Developer portal → Membership) |
| `APPLE_APP_SPECIFIC_PASSWORD` | An app-specific password for your Apple ID ([appleid.apple.com](https://appleid.apple.com) → Sign-In and Security → App-Specific Passwords) |

To get the certificate and its base64 value (do this once, on any Mac with
your Developer ID certificate installed in Keychain Access, or via
Xcode → Settings → Accounts → Manage Certificates):

```bash
# Export the certificate + private key from Keychain Access as a .p12 file
# (File > Export Items..., choose "Personal Information Exchange (.p12)")
# then run:
base64 -i DeveloperIDCertificate.p12 | pbcopy
# paste the clipboard contents as the value of APPLE_CERTIFICATE_P12
```

Once those secrets are set, re-run the workflow — it will sign with your
Developer ID and notarize with Apple automatically, and the resulting app
opens with no warning at all.

---

## Option B — Build locally on a Mac

If you have access to a Mac (yours or a lab machine):

### Prerequisites
- macOS
- Python 3 installed (`python3 --version` in Terminal). Get it from
  [python.org](https://www.python.org/downloads/macos/) if needed — the
  Xcode Command Line Tools' Python is not sufficient for Tkinter apps.
- This project folder, including the `Problems` folder

### First-time build

```bash
cd ~/Documents/"Python Review - Student"      # or wherever you placed the folder
chmod +x build_mac.sh
./build_mac.sh
```

Result: `dist/StudentPythonReview.app`

### Rebuild after changing the app

```bash
./build_mac.sh --skip-install
```

### Build and sign with your Developer ID in one step

```bash
./build_mac.sh --sign "Developer ID Application: Your Name (ABCDE12345)"
```

Find your exact identity string with:

```bash
security find-identity -v -p codesigning
```

### Notarize a locally-built app (optional, removes the Gatekeeper warning)

```bash
ditto -c -k --sequesterRsrc --keepParent dist/StudentPythonReview.app notarize.zip
xcrun notarytool submit notarize.zip --apple-id "you@example.com" \
  --team-id "ABCDE12345" --password "app-specific-password" --wait
xcrun stapler staple dist/StudentPythonReview.app
```

(Create an app-specific password at [appleid.apple.com](https://appleid.apple.com)
→ Sign-In and Security → App-Specific Passwords. Your Team ID is on the
[Apple Developer portal](https://developer.apple.com/account) under Membership.)

---

## Distributing to students

1. Compress the `.app`: right-click `StudentPythonReview.app` in Finder →
   **Compress "StudentPythonReview.app"** (or use the `ditto` command shown
   by `build_mac.sh`). Share the resulting `.zip` (via LMS, email, shared
   drive, etc.) — never share the bare `.app` through services that mangle
   Mac file bundles (e.g. some USB transfers to Windows).
2. Students unzip it and double-click `StudentPythonReview.app`.
3. **If the app is ad-hoc signed (no Developer ID secrets configured):**
   the first launch will show "Apple could not verify... is free of malware"
   or "unidentified developer." Students should **right-click (or
   Control-click) the app → Open**, then confirm **Open** in the dialog.
   This is a one-time step per machine.
4. **If the app is signed with your Developer ID and notarized:** it opens
   normally with a plain double-click, no warning.

---

## How the code adapts to macOS

You generally do not need to change the application code — it already
handles platform differences:

- `CodeReview.py` → `app_base_dir()` uses `pathlib` and checks
  `sys.frozen`/`sys._MEIPASS` so the `Problems` folder is found correctly
  whether you run `python3 CodeReview.py` directly or run the packaged
  `.app` (macOS) or `.exe` (Windows).
- `CoffeeCanvas.py` → `Window.__init__` sets `self.MacOS = (platform.system()
  == 'Darwin')`. This is used by `checkDarkMode()`, which reads
  `defaults read -g AppleInterfaceStyle` on macOS and the Windows registry
  (`winreg`) on Windows — the `winreg` import is wrapped so it's simply
  skipped on macOS.
- All file paths use `pathlib.Path` with `/` joins, which works on both
  operating systems.

If you introduce new code that is Windows- or macOS-specific in the future,
follow the same pattern: check `platform.system() == 'Darwin'` (or use
`self.MacOS` inside `CoffeeCanvas`/`CoffeeBean` classes) and branch
accordingly, keeping the Windows-only import inside a `try/except ImportError`.

---

## What gets packaged

- Entry point: `CodeReview.py`
- Local modules: `SafeNodeVisitorClass`, `CoffeeBean`, `CoffeeCanvas`, `CoffeeColors`
- Data: the entire `Problems` folder
- Runtime helpers: `tkinter` (built into Python), `Pillow` (`PIL`) if installed

You do **not** need to include helper/test files such as `CodeTestOne.py` or
`Helpful Text Answers.py` unless you start importing them from the app.

### Changing the build (name, icon, version)

Edit `StudentPythonReview-mac.spec`:

- `name='StudentPythonReview'` in the `EXE(...)` and `COLLECT(...)` sections —
  the internal executable name.
- `BUNDLE(... name='StudentPythonReview.app' ...)` — the visible app name.
  Change this to rename the `.app` students see, e.g.
  `name='CIS 130 Code Review.app'`.
- `info_plist={...}` — `CFBundleDisplayName`, `CFBundleShortVersionString`,
  etc. Bump `CFBundleShortVersionString`/`CFBundleVersion` each time you
  hand out a new build so students can tell versions apart.
- Icon: the app already ships with `AppIcon.icns` (a green `</>` code badge
  with a checkmark), wired up via `icon='AppIcon.icns'` in the `BUNDLE(...)`
  block. To use your own icon instead, just replace `AppIcon.icns` with a
  new file of the same name — no spec changes needed. To make an `.icns`
  from a `.png` on a Mac:
  ```bash
  mkdir AppIcon.iconset
  sips -z 512 512   your_icon.png --out AppIcon.iconset/icon_512x512.png
  sips -z 256 256   your_icon.png --out AppIcon.iconset/icon_256x256.png
  sips -z 128 128   your_icon.png --out AppIcon.iconset/icon_128x128.png
  sips -z 32 32     your_icon.png --out AppIcon.iconset/icon_32x32.png
  sips -z 16 16     your_icon.png --out AppIcon.iconset/icon_16x16.png
  iconutil -c icns AppIcon.iconset -o AppIcon.icns
  ```

---

## Directions for modifying components of the program

The app is split into a few focused files. Knowing what lives where makes it
easy to change behavior without breaking the rest of the app.

### `CodeReview.py` — the app itself (entry point)
This is where you'd make almost all content and behavior changes:
- **`class CodeReview`** builds the whole window: title, line numbers, the
  three text boxes (Instructions / Edit Code / Result), the category combo
  box, and the NEXT / SUBMIT / QUIT buttons, then wires up their callbacks.
- **Program mode flags** near the top of `__init__`:
  - `self.development = True` — enables Control-Click (redo current problem)
    and Shift-Control-Click (redo but keep edited code) on the NEXT button.
    Set to `False` for a clean student build with no hidden shortcuts.
  - `self.randomIndexActivated` — `True` randomizes problem order within a
    category; `False` presents them in file/name order.
- **`extractProblem()` / `getSelectionsFromFolder()`** — parse the `Problems/*.txt`
  files (JSON header + Python code body) into the in-memory problem list.
  Change this if you alter the problem file format.
- **`preCheck()` / `preCheckTheUnsafe()`** — the keyword allow/deny lists
  applied to student code before it runs. Add or remove forbidden/required
  keywords here if you want to loosen or tighten what students may write.
- **`processingSafePython()` / `unsafePythonProcessing()`** — how submitted
  code is executed and graded: the safe path routes through
  `SafeNodeVisitor.safe_exec()`; the unsafe path (`UnsafeCode: true` in a
  problem's JSON) runs with plain `exec()` and captures stdout/stderr into
  the response box.
- **`checkTheAnswer()` / `calculateTheGrade()`** — answer comparison logic
  and the letter-grade thresholds (currently 93/90/87/83/80/77/73/70/67/63/60).
  Adjust the percentage cutoffs here to match your syllabus.
- **Button handlers** — `Next()`, `Submit()`, `Quit()` at the bottom of the
  class are the click handlers wired to `CanvasButton` in `__init__`.

### `Problems/Problem_NN.txt` — the question bank
Each file is a JSON object (permissive parser — see `extractProblem()`,
not strict JSON) followed by a Python code stub, e.g.:

```
{
    "Title": "What are the Possibilities?",
    "Category": "Math",
    "Imports": "math, random, datetime",
    "Required": ["answer"],
    "Exclude": [],
    "Parameters": [5000, 99],
    "Return": 15,
    "UnsafeCode": false,
    "Instructions": "Set the variable called ~answer~ ... "
}
def myFunction(a,b):
    ...
    return answer
```
- Add a new problem by copying an existing `.txt`, changing `Title`,
  `Category`, `Instructions`, `Parameters`, `Return`, and the code body.
- `~` inside `Instructions` is converted to a single quote `'` at display
  time (quotes get lost when the loose JSON parser reads the file).
- `Category` groups problems in the category dropdown; `"Everything"` is
  added automatically as the first option.
- `Required` / `Exclude` are keyword allow/deny lists checked before running
  the student's code (see `preCheck()` in `CodeReview.py`).
- `UnsafeCode: true` runs the code with real Python `exec()` (stdout/stderr
  shown to the student) instead of the restricted AST-checked path — use
  sparingly, and only for exercises intentionally covering `os`/`sys`/file I/O.
- After editing problem files, just rebuild — no `.spec` changes needed since
  the entire `Problems` folder is bundled as data.

### `SafeNodeVisitorClass.py` — sandboxing for "safe" code
`SafeNodeVisitor` walks the AST of submitted code and rejects anything not in
`SAFE_NODES` (a whitelist of allowed Python syntax nodes) or `SAFE_NAMES` (a
whitelist of allowed variable/function names: `a, b, c, x, y, z, int, bool,
float, sum, min, max`, plus any names added via `setVariables()`/`Variables`
in the problem JSON). Edit `SAFE_NODES`/`SAFE_NAMES` here if you want to allow
or block specific Python language features program-wide (this affects every
problem that doesn't use `UnsafeCode: true`).

### `CoffeeColors.py` — the color palette
`ColorClass` defines named colors (`"DarkGreen"`, `"LightYellow"`, `"Mist"`,
etc.) used throughout `CodeReview.py` and `CoffeeCanvas.py`. Add new named
colors here if you want new options for backgrounds/buttons/text without
hunting for raw hex codes elsewhere.

### `CoffeeCanvas.py` — the drawing/window/widget engine
A general-purpose Tkinter Canvas graphics library (not specific to this app —
also used by the author's other class projects). Key pieces you'll touch most:
- **`Window`** — the top-level app window; owns dark-mode/macOS detection
  (`self.MacOS`, `checkDarkMode()`).
- **`Canvas`** — the drawing surface that holds every visual object; has
  `forEventAddFunction()` for binding keyboard/mouse events (e.g. `<Return>`,
  `<ComboboxSelected>` used in `CodeReview.py`).
- **`CanvasButton`, `CanvasTextBox`, `ComboBox`, `Frame`** — the higher-level
  widgets `CodeReview.py` builds the UI from.
- **`Text`, `Rectangle`, `Circle`, `Image`, `Polygon`, `Squaricle`, etc.** —
  low-level drawable primitives; the `Smart*` variants (`SmartText`,
  `SmartSquaricle`, ...) add click/hover interactivity via `ActionInterface`.
- **`Popup`, `OkPopup`, `YesNoPopup`** — ready-made modal dialogs if you want
  to add confirmation prompts (e.g. "Are you sure you want to quit?").
Only change this file if you need a new kind of widget or drawable shape;
most content/behavior changes belong in `CodeReview.py` instead.

### `CoffeeBean.py` — form widgets & validation
A companion library of `ttk`-based form controls with built-in validation
mixins: `Entry`, `ComboBox`, `RadioBox`, `SpinBox`, `CheckBoxes`, `TextBox`,
plus validity mixins like `UsDateMixin`, `NumberMixin`, `NonblankMixin`,
`PasswordMixin` that combine into ready types (`ValidEntryUsDate`,
`ValidSpinBox`, etc.). This app doesn't use most of these directly (it's
mainly Canvas-based via `CoffeeCanvas.py`), but it's available if you add
traditional form-style input elsewhere in the program.

### Testing changes before rebuilding
Run the app directly with Python to iterate quickly, without waiting on a
full PyInstaller build each time:
```bash
python3 CodeReview.py
```
Only run `build_mac.sh` (or the GitHub Actions workflow) once you're ready to
produce a new `.app` to hand out.
>>>>>>> ea344ee49bb091beacc3d996061ea4950c9aab05
