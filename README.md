# Monokular

Monokular — because it does one thing and does it well: export PDF pages as images with a preview option.

## Features

- Open PDF files via toolbar, drag & drop, or command line
- Selectable page thumbnails in a responsive grid
- Preview pages with zoom (Ctrl+Click or Preview button)
- Export selected pages as PNG or JPEG
- Configurable quality and PPI (72–1200)
- Remembers window size between sessions

## Keyboard Shortcuts

- `Ctrl+Q` — Quit
- `Ctrl+Click` — Preview a page

## Usage (local)

```bash
pip install -r requirements.txt
python main.py
```

Open a PDF from the command line:

```bash
python main.py /path/to/file.pdf
```

## Build a standalone binary (PyInstaller)

```bash
pip install pyinstaller
pyinstaller monokular.spec
```

The binary will be at `dist/monokular`.

## Install on Arch Linux (AUR)

```bash
yay -S monokular
```

Or manually:

```bash
git clone https://aur.archlinux.org/monokular.git
cd monokular
makepkg -si
```

## Build from source (PKGBUILD)

1. Create a source tarball:

```bash
tar czf monokular-1.0.0.tar.gz --transform='s,^,monokular-1.0.0/,' \
    main.py requirements.txt monokular.desktop PKGBUILD \
    assets/icon.svg app/*.py
```

2. Build and install:

```bash
makepkg -si
```

After installation, the following files are placed automatically:

- `/usr/bin/monokular` — launcher script
- `/usr/lib/monokular/` — app files
- `/usr/share/applications/monokular.desktop` — desktop entry
- `/usr/share/icons/hicolor/scalable/apps/monokular.svg` — app icon

3. Run:

```bash
monokular
```

## Linux desktop integration (manual)

For local (non-packaged) use, copy the desktop file:

```bash
cp monokular.desktop ~/.local/share/applications/
```

Edit `Exec` and `Icon` paths in the desktop file to point to your local install.

## Requirements

- Python 3.10+
- PyQt6
- PyMuPDF
