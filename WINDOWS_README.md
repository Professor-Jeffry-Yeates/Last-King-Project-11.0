# Build a standalone Last King app on your Windows PC

Build this on the PC. The game repository has no GitHub Actions workflow, and this page does not add one.

Run the commands in PowerShell. `call`, `cd /d`, and `%USERPROFILE%` are Command Prompt syntax. PowerShell reports `call` as not recognized.

The source is https://github.com/Professor-Jeffry-Yeates/Last-King-Project-11.0, branch `main`, commit `825a9a3` (`Added icon`). That tree is Python modules plus the `Quiz_Content` folder. It has no `requirements.txt`, `pyproject.toml`, `setup.py`, PyInstaller `.spec`, or other packager script. Nothing in the clone writes a `.exe`.

`ClassIntro.py` is the program. It calls `SetupGameClass("Quiz_Content", ...)`. `SetupGameClass.py` imports `SoundMixerClass`, and `SoundMixerClass.py` imports `pygame`. The window is Tk: `CoffeeCanvas.py` creates `tk.Tk()`. `MiniAudioSoundMixerClass.py` is comments, including `import miniaudio`. This build stays on pygame.

## 1. Install Python 3.13.16 (64-bit)

The repository does not pin a Python version. `.gitignore` only ignores `__pycache__/*.cpython-314.pyc`. `PYGAME_README.md` describes Python 3.15.0.

`SoundMixerClass.py` needs pygame 2.6.1, the version named in `PYGAME_README.md`. On PyPI, the Windows wheels for that release stop at Python 3.13. The 64-bit file is `pygame-2.6.1-cp313-cp313-win_amd64.whl`. There is no `cp314` or `cp315` wheel, so Python 3.14 and 3.15 will not install that file.

`PYGAME_README.md` also describes a Windows source build of pygame 2.6.1 for Python 3.15, using Visual Studio 2022 Build Tools and two patch files, `patches/pygame-2.6.1-python315.patch` and `patches/pygame-2.6.1-setuptools-82.patch`. This clone has no `patches` directory and no `scripts` directory, so those steps have nothing to apply. Use the 3.13 wheel instead. A C++ compiler is not part of this build.

Install the 64-bit installer:

https://www.python.org/downloads/release/python-31316/

https://www.python.org/ftp/python/3.13.16/python-3.13.16-amd64.exe

On the first installer screen, check **Add python.exe to PATH** and **Use admin privileges when installing py.exe**. On the optional-features screen, leave **tcl/tk and IDLE** and **py launcher** checked. The game window is Tk, and the commands below use the `py` launcher.

In PowerShell:

```powershell
py -3.13 -V
```

The line must start with `Python 3.13.16`.

## 2. Clone the game

Install Git for Windows if `git` is not already on the PC (https://git-scm.com/download/win). In PowerShell:

```powershell
git clone https://github.com/Professor-Jeffry-Yeates/Last-King-Project-11.0.git "C:\Users\Jeffy\Midterm\Last-King-Project-11.0"
Set-Location "C:\Users\Jeffy\Midterm\Last-King-Project-11.0"
```

`QuizClass.py` opens `Quiz_Content\Instructions.json` from the current directory first. Every later command that runs the game or the packager starts in this folder.

## 3. Install pygame 2.6.1 and Pillow

Create the virtual environment outside the clone, with that same Python 3.13.16. In PowerShell:

```powershell
py -3.13 -m venv "C:\Users\Jeffy\Midterm\last-king-py313"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& "C:\Users\Jeffy\Midterm\last-king-py313\Scripts\Activate.ps1"
python -m pip install --upgrade pip
python -m pip install pygame==2.6.1 Pillow
```

`Set-ExecutionPolicy` applies only to this PowerShell window, so `Activate.ps1` is allowed to run. If the `py -3.13 -m venv` line already succeeded, skip it and run the rest of the block.

`pip` must install the wheel, not a source tree. A line that says it is building `pygame-2.6.1.tar.gz` means this environment is not Python 3.13. Stop and check `python -V`.

Pillow has no version pin in the repository. Install it anyway. `MapClass.py`, `QuestionAreaClass.py`, `DataClass.py`, and `DebuggingClass.py` call `PILImage`. `CoffeeCanvas.py` imports Pillow when it is installed. Without it, `MapClass.py` still calls `PILImage.open` while loading a map.

Check the imports with this environment:

```powershell
python -c "import pygame, PIL, tkinter; print(pygame.version.ver); print(pygame.__file__)"
```

`pygame.version.ver` must be `2.6.1`, and `pygame.__file__` must sit under `C:\Users\Jeffy\WindowsPythonMidterm\Midterm\last-king-py313`.

Leave these packages out:

- `appscript` and `mactypes` are imported by `Mac_PlatformSpecific.py`. On Windows, `QuizClass.py` imports `PC_PlatformSpecific.py` instead.
- `miniaudio` and `numpy` are only mentioned in the commented `MiniAudioSoundMixerClass.py`.
- `pywin32` is the optional Outlook helper named in a comment in `PC_PlatformSpecific.py`. The window opens without it. `sendEmail` is the function that needs `win32com.client`.
- Do not install `pyodbc`. `DatabaseClasses.py` line 4 imports it on Windows while the game is loading (`ClassIntro.py` → `SetupGameClass` → `DebuggingClass` → `QuestionAreaClass`). This quiz never reaches `pyodbc.connect` (line 58); that call runs only from `QuestionAreaClass.SQLProcessing` when a question language is `sql`, and `Quiz_Content` has no SQL question. The `##pip install pyodbc` lines in `Quiz_Content\Import Readme.md` are comments. In `C:\Users\Jeffy\WindowsPythonMidterm\Midterm\Last-King-Project-11.0\DatabaseClasses.py`, replace the platform test at the top with:

```python
if sys.platform.lower() == "darwin":
    import random as pyodbc # Stop the error but may crash - DB not implemented for MacOS
```

## 4. Run it from source

From the clone root, with the virtual environment still active:

```powershell
Set-Location "C:\Users\Jeffy\Midterm\Last-King-Project-11.0"
python ClassIntro.py
```

`Quiz_Content\Instructions.json` names the window "Last King - Python" and the title "Python Midterm". `SetupGameClass.py` opens that window at 1350 by 850. Sound starts through pygame. If the import check in section 3 failed, this command will fail in the same place.

## 5. The .exe is not set up yet

Two pieces are missing. Both are local. Neither belongs in GitHub Actions.

**The entry script never calls** `multiprocessing.freeze_support()`**.** `DataClass.py` creates `multiprocessing.Lock` while the game is starting (`codingLock` and `graphicLock`). On Windows, a PyInstaller executable that creates those locks raises `RuntimeError` and starts extra copies of itself unless `freeze_support()` runs first. Put these two lines at the top of `ClassIntro.py`, above the other imports:

```python
import multiprocessing
multiprocessing.freeze_support()
```

`freeze_support()` returns immediately when you run `python ClassIntro.py`. Run section 4 again after the edit and confirm the window still opens.

**Nothing invokes PyInstaller.** The source already has the matching runtime checks, and no file calls the packager:

- `resource_path.py` reads `sys._MEIPASS`.
- `QuizClass.py` checks `sys.frozen`. When the current-directory open of `Quiz_Content\Instructions.json` fails, it opens `Quiz_Content` from `sys._MEIPASS`.
- `Audio README.md` mentions `PyInstaller` only for `--collect-all miniaudio` on macOS. That mixer is not the one this game imports.

Install PyInstaller into the same environment and pack from the clone root:

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --name ClassIntro --add-data "Quiz_Content;Quiz_Content" ClassIntro.py
```

That is the command that writes the executable. The semicolon is the Windows separator for `--add-data`. The destination `Quiz_Content` is the folder name `QuizClass` joins onto `sys._MEIPASS`. PyInstaller is not pinned in the repository. Use the current release that `pip` installs for this Python 3.13.

The executable is:

```text
C:\Users\Jeffy\Midterm\Last-King-Project-11.0\dist\ClassIntro\ClassIntro.exe
```

PyInstaller’s default is an onedir folder, which is what that command writes. The same command also writes `build\` and `ClassIntro.spec` next to the sources. Run it:

```powershell
Set-Location "C:\Users\Jeffy\Midterm\Last-King-Project-11.0\dist\ClassIntro"
.\ClassIntro.exe
```

A console window stays open beside the game. A missing `Quiz_Content` file is printed there. After the game window opens, rebuild with `--windowed` added to the PyInstaller command when you want that console gone.

`LastKing_ico.png` is a PNG. This command does not pass `--icon`. PyInstaller’s Windows icon option reads an `.ico` file, and the clone does not contain one.

`No Picture Warning.png` sits at the clone root. `QuestionAreaClass.py` opens that bare name from the current directory when a picture file is missing. It does not go through `resource_path.py`. Copy the PNG into `dist\ClassIntro` if you want that fallback next to the exe.

Rebuild after you change code or assets. `ClassIntro.spec` remembers the `--add-data` path. From the clone root, with the environment active:

```powershell
Remove-Item -Recurse -Force build, dist
python -m PyInstaller --noconfirm ClassIntro.spec
```

Run section 4’s `python ClassIntro.py` when you only changed Python and want to try it before packing. The spec file is generated by the first PyInstaller command. If you have not saved that edit to `ClassIntro.py`, run the full `--add-data` command from this section again instead.
