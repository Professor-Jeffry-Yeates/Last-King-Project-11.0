# Build pygame for Python 3.15.0

Python 3.15.0 removed `PyWeakref_GetObject` from the C API. [pygame 2.6.1](https://pypi.org/project/pygame/2.6.1/), the current release on PyPI, still calls it in four places:

- `src_c/surface.c` in `surf_get_locks`
- `src_c/surface.c` in `_release_buffer`
- `src_c/surflock.c` in `pgSurface_UnlockBy` (two calls)

GCC then stops the build with:

```text
src_c/surface.c:1023:15: error: implicit declaration of function ‘PyWeakref_GetObject’; did you mean ‘PyWeakref_GetRef’?
```

That message is the whole “needs an older C++” symptom. `PyWeakref_GetObject` is gone from libpython, so an older C++ standard or an older GCC cannot make this source link. The replacement, `PyWeakref_GetRef`, has been in the stable ABI since Python 3.13. It returns `1` and a new reference when the referent is alive, `0` and `NULL` when the weak reference is dead, and `-1` on error. Upstream pygame has not shipped that change yet ([pygame#4716](https://github.com/pygame/pygame/issues/4716)).

There is no `cp315` wheel for pygame 2.6.1. `pip install pygame` on Python 3.15 downloads the source tarball and hits this error. Two ways through it are below.

## Use a prebuilt wheel

[pygame-ce](https://pypi.org/project/pygame-ce/) 2.5.8 publishes Python 3.15 wheels for Windows, macOS, and Linux, and it is imported as `pygame`.

```bash
python3.15 -m pip uninstall pygame
python3.15 -m pip install pygame-ce
python3.15 -c "import pygame; print(pygame.version.ver)"
```

This installed and imported as pygame-ce 2.5.8 on Python 3.15.0 here. Use this when you want pygame without a C toolchain.

## Build pygame 2.6.1 from source

Use the PyPI source tarball, `pygame-2.6.1.tar.gz`. It already contains the generated C for the Cython modules. A fresh Cython 3.3 run of the `.pyx` files fails earlier, in `src_c/cython/pygame/_sprite.pyx`, with `Illegal use of special attribute __dict__`. Leave Cython out of the build.

Apply both patches in this repo, then install:

- `patches/pygame-2.6.1-python315.patch` replaces the four `PyWeakref_GetObject` calls. On Python 3.15 and newer it uses `PyWeakref_GetRef` and keeps the reference counts straight (a dead lock becomes `None` in `get_locks`, and a new reference from `GetRef` is released). Older Python keeps the original calls, so the same tree still builds there.
- `patches/pygame-2.6.1-setuptools-82.patch` calls `distutils.spawn.spawn` from `setup.py`. setuptools 82 changed `CCompiler.spawn`, and a current pip (setuptools 84 was used for the build below) otherwise dies in that monkeypatch. The same one-line change is what Fedora carries for setuptools 82+.

### Linux

Install a C compiler, Python 3.15 headers, and the SDL libraries pygame links against. A python.org or [uv](https://docs.astral.sh/uv/) install of Python 3.15 already includes its headers. A distro Python needs the matching `-devel` / `-dev` package.

Debian or Ubuntu:

```bash
sudo apt install build-essential pkg-config \
  libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
  libfreetype6-dev libjpeg-dev libpng-dev libportmidi-dev
```

Fedora already ships a patched pygame 2.6.1 for Python 3.15 (`python3-pygame` on Fedora 45). To build it yourself:

```bash
sudo dnf install gcc pkgconf-pkg-config python3-devel \
  SDL2-devel SDL2_image-devel SDL2_mixer-devel SDL2_ttf-devel \
  freetype-devel libjpeg-turbo-devel libpng-devel portmidi-devel
```

From this repository, with `python3.15` on `PATH`:

```bash
chmod +x scripts/build-pygame-3.15.sh
PYTHON=python3.15 ./scripts/build-pygame-3.15.sh
```

The script sets `PYGAME_DETECT_AVX2=1` so an x86-64 build includes the AVX2 blitters. Without that, importing pygame prints a performance warning on AVX2 machines.

Or by hand, from a temporary directory:

```bash
python3.15 -m pip download pygame==2.6.1 --no-binary=:all: -d /tmp/pygame-src
tar -xzf /tmp/pygame-src/pygame-2.6.1.tar.gz -C /tmp/pygame-src
cd /tmp/pygame-src/pygame-2.6.1
patch -p1 < /path/to/this/repo/patches/pygame-2.6.1-python315.patch
patch -p1 < /path/to/this/repo/patches/pygame-2.6.1-setuptools-82.patch
python3.15 -m pip install --upgrade pip setuptools wheel
PYGAME_DETECT_AVX2=1 python3.15 -m pip install .
```

### macOS

Install the Xcode command line tools and the SDL libraries, then run the same script. The patches are the same ones verified on Linux.

```bash
xcode-select --install
brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf pkg-config
PYTHON=python3.15 ./scripts/build-pygame-3.15.sh
```

### Windows

Install the current Visual Studio 2022 Build Tools and select the “Desktop development with C++” workload (MSVC v143 and a Windows 10 or 11 SDK). Official CPython 3.15 Windows binaries are built with that compiler family. An older Visual Studio toolset does not restore `PyWeakref_GetObject`.

In a “x64 Native Tools Command Prompt”, from an unpacked and patched `pygame-2.6.1` directory:

```bat
py -3.15 -m pip install --upgrade pip setuptools wheel
py -3.15 -m pip install .
```

Download and patch with the same two `patch -p1` commands as on Linux (Git for Windows includes `patch`). If the build stops inside `buildconfig/vstools.py` with `No module named distutils.msvccompiler` before any pygame C file is compiled, that is a separate setuptools 80+ import-path change ([pygame#4777](https://github.com/pygame/pygame/issues/4777)). The Python 3.15 wheel from pygame-ce avoids that Windows build script.

## Check the install

```bash
python3.15 -c "import pygame; print(pygame.version.ver, pygame.version.SDL)"
```

A source build of pygame 2.6.1 prints `2.6.1` and the SDL version you linked. The pygame-ce wheel prints `2.5.8`.

This source build was compiled and imported on Linux x86_64 with Python 3.15.0, GCC 13.3, SDL 2.30.0, and setuptools 84.0.0. After `SDL_VIDEODRIVER=dummy`, `pygame.init()`, a 32×32 surface fill, `Surface.lock`, `Surface.get_locks`, and `Surface.unlock` all ran. `get_locks` is one of the functions the patch rewrites.
