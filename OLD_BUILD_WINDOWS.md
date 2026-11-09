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
