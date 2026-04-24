# Sharpshooter — Design Document

> Architecture overview and research notes for planned improvements.

---

## 1. Current Architecture

Sharpshooter is a minimal terminal-based file manager written in pure Python 3 with zero
external dependencies. It follows an MVC-like structure:

```
sharpshooter.py          Entry point, wraps curses.wrapper()
controller.py            Main event loop; maps keys → actions; coordinates re-render
content.py               All application state (cwd, selection, clipboard, undo queue)
file_system.py           All file I/O (list, copy, move, delete, zip, open, terminal)
config_manager.py        Reads/writes ~/.sharpshooter_config (INI format)
pane_manager.py          Layout: 3 panes + header + footer; delegates to pane objects
cursed_files_pane.py     Renders one curses window (file list, scrolling, attributes)
single_line_window.py    Renders a single header/footer line
input_keys.py            Loads hotkeys from config; generates on-screen help text
fs_item.py               Data class for a file/folder entry
utility.py               Pure text/path helpers
file_system_error.py     Custom exception with user-friendly messages
```

### Layout

```
┌──────────────────────────────────────────────────┐
│  /current/path/                        [header]  │
├──────────────┬───────────────┬───────────────────┤
│  parent dir  │   cwd files   │  child preview    │
│  (1/3 width) │   (1/3 w)     │  (1/3 w)          │
├──────────────┴───────────────┴───────────────────┤
│  Last action description             [status]    │
├──────────────────────────────────────────────────┤
│  f-new  r-rename  z-zip  …           [hotkeys]   │
└──────────────────────────────────────────────────┘
```

### Event loop

```
while running:
    pane_manager.render_panes()
    key = stdscr.getch()
    controller.process_input(key)   # → content.py → file_system.py
```

### What works well

- ~1 000 LOC total; easy to read end-to-end.
- No external dependencies means zero install friction for the engine itself.
- Background threading for zip keeps the UI responsive.
- Undo via a `LifoQueue` capped at 128 items.
- Config auto-created on first run with sensible defaults.

### Current pain points

| Area | Problem |
|------|---------|
| Cross-platform | Terminal open, trash, file-open are Linux/XFCE-biased |
| Rendering | Raw curses: manual coordinate math, hard to extend |
| Install | Snap and .deb only; no one-liner for macOS or non-Ubuntu users |
| Config | INI format can't express themes, file-type rules, or custom commands |

---

## 2. Cross-Platform Action Execution

### 2.1 Open terminal

**Current code** (`file_system.py`): tries a hardcoded list —
`exo-open → x-terminal-emulator → gnome-terminal → xfce4-terminal → konsole → urxvt` —
with no pre-flight check and no macOS or WSL path.

**Recommended approach**

```
1. Detect platform with sys.platform ('darwin' / 'linux').
2. On Linux, read $XDG_CURRENT_DESKTOP to pick the DE-native terminal first.
3. Use shutil.which() to check each candidate before trying it.
4. Fall back through a priority list; last resort: xterm.
```

**Priority lists**

| Platform | Order |
|----------|-------|
| macOS | `$TERM_PROGRAM` (reuse parent), `open -a iTerm`, `open -a Terminal` |
| GNOME | `gnome-terminal`, `kitty`, `alacritty`, `xterm` |
| KDE | `konsole`, `kitty`, `alacritty`, `xterm` |
| XFCE | `xfce4-terminal`, `kitty`, `alacritty`, `xterm` |
| Generic Linux | `exo-open --launch TerminalEmulator`, `x-terminal-emulator`, `kitty`, `alacritty`, `urxvt`, `xterm` |
| WSL | `wt.exe` (Windows Terminal), then generic Linux list |

```python
import sys, os, shutil, subprocess

def _detect_platform():
    if sys.platform == 'darwin':
        return 'macos'
    try:
        if 'microsoft' in open('/proc/version').read().lower():
            return 'wsl'
    except OSError:
        pass
    return 'linux'

def _de_terminal_candidates():
    de = os.getenv('XDG_CURRENT_DESKTOP', '').lower()
    if 'gnome' in de:
        return ['gnome-terminal', 'kitty', 'alacritty']
    if 'kde' in de:
        return ['konsole', 'kitty', 'alacritty']
    if 'xfce' in de:
        return ['xfce4-terminal', 'kitty', 'alacritty']
    return ['exo-open --launch TerminalEmulator', 'x-terminal-emulator',
            'kitty', 'alacritty', 'urxvt']

def open_terminal(directory):
    platform = _detect_platform()
    if platform == 'macos':
        candidates = [['open', '-a', 'iTerm', directory],
                      ['open', '-a', 'Terminal', directory]]
    elif platform == 'wsl':
        candidates = [['wt.exe', '-d', directory]]
        candidates += [[t, '--working-directory', directory]
                       for t in _de_terminal_candidates() if shutil.which(t)]
    else:
        candidates = [[t, '--working-directory', directory]
                      for t in _de_terminal_candidates() if shutil.which(t)]
        candidates.append(['xterm'])

    for cmd in candidates:
        try:
            subprocess.Popen(cmd, cwd=directory,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except OSError:
            continue
```

### 2.2 Open file with default app

**Current code**: tries `xdg-open` then `open` blindly.

**Better approach**: branch on `sys.platform` first, suppress output.

```python
def open_file(path):
    if sys.platform == 'darwin':
        cmd = ['open', path]
    else:  # linux / wsl
        cmd = ['xdg-open', path]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
```

For WSL, `xdg-open` typically works via `xdg-open` → `wslview` (if wslu is installed).
If it isn't, fall back to `wsl-open` or `cmd.exe /c start`.

### 2.3 Delete / trash

**Current code**: manually moves files to `~/.local/share/Trash/files/` — Linux-only,
ignores the `.info` metadata files required by the Freedesktop Trash spec.

**Recommended**: add `send2trash` (a single small dependency with no transitive deps).

```python
from send2trash import send2trash   # pip install send2trash

def delete(path):
    send2trash(str(path))           # uses native API on all platforms
```

`send2trash` uses:
- **macOS**: `FSMoveObjectToTrashSync` (Cocoa native)
- **Linux**: Freedesktop spec (`.info` files written correctly)
- **Windows**: Recycle Bin

This is the only intentional external dependency introduced. Keep the current
`LifoQueue` undo stack but store the original path for restoration
(`shutil.move(trash_path, original_path)`).

### 2.4 Zip / archive

`shutil.make_archive()` and `shutil.unpack_archive()` are cross-platform and
sufficient for the current feature set. Two improvements worth making:

1. **Support `.tar.gz` in addition to `.zip`** so Linux users get the idiomatic format.
   Auto-detect from the extension when unzipping; prompt when zipping.
2. **Progress callback**: drop down to `zipfile` / `tarfile` directly so a callback
   can update the UI (useful for large archives).

### 2.5 OS / distro detection module

Introduce a small `platform_utils.py`:

```python
import sys, os

def platform_type():
    """Returns 'macos' | 'linux' | 'wsl'."""
    if sys.platform == 'darwin':
        return 'macos'
    try:
        if 'microsoft' in open('/proc/version').read().lower():
            return 'wsl'
    except OSError:
        pass
    return 'linux'

def desktop_environment():
    return os.getenv('XDG_CURRENT_DESKTOP', '').lower()
```

---

## 3. TUI Rendering Library

### Options evaluated

| Library | Paradigm | Migration effort | Performance | Maintenance | File manager fit |
|---------|----------|-----------------|-------------|-------------|-----------------|
| **curses** (current) | Low-level, manual | — | Good | Stdlib, frozen | Works but verbose |
| **blessed** | Curses wrapper | Low | Excellent | Active (2026) | Minor wins only |
| **urwid** | Widget-based | Medium | Adequate | Maintained | Good |
| **Textual** | Reactive, CSS-like | High | 120 FPS | Very active | Excellent |
| **Rich** | Output rendering | N/A (not interactive) | Good | Very active | Not suitable alone |

### Recommendation: Textual

Textual (by Textualize) is the right target for a rewrite of the rendering layer.

**Why:**
- The 3-pane layout maps directly onto Textual's `Columns` + `Container` system.
- `Input` widget replaces the manual `curses.textpad.Textbox`.
- `Footer` widget replaces the hand-rolled hotkey guide.
- CSS-based theming replaces `curses.color_pair` bookkeeping.
- Reactive data binding reduces the "render everything on every keypress" pattern.
- 120 FPS rendering vs curses' ~20 FPS, with dirty-region delta updates.

**What to keep:**
- All business logic in `content.py` and `file_system.py` is rendering-agnostic and
  can be kept almost unchanged.
- The event loop in `controller.py` collapses into Textual's `on_key` handlers.

**Migration sketch:**

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DirectoryTree
from textual.containers import Horizontal

class SharpshooterApp(App):
    CSS = """
    Horizontal { height: 1fr; }
    FilePane { width: 1fr; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield FilePane(id="left")   # parent dir
            yield FilePane(id="main")   # cwd
            yield FilePane(id="right")  # child preview
        yield Footer()

    def on_key(self, event):
        self.content.handle(event.key)
        self.query_one("#main").refresh()
```

**Phased approach** (to avoid a big-bang rewrite):
1. Phase 1 — keep curses, extract all rendering into a `Renderer` interface.
2. Phase 2 — implement `TextualRenderer` behind the interface; ship as opt-in.
3. Phase 3 — make Textual the default; drop curses renderer.

**Alternative if zero new dependencies is a hard requirement:** `blessed` replaces
curses with a nicer API (full color, clean key names, proper resize handling) with no
new abstractions. It is a drop-in for about 80 % of what the current code does.

---

## 4. Installation & Distribution

### Approaches evaluated

| Method | One-liner | No Python required | No root | Easy update | No app-store |
|--------|-----------|-------------------|---------|-------------|-------------|
| pipx from git | ✅ | ❌ | ✅ | ✅ | ✅ |
| uv tool from git | ✅ | ❌ | ✅ | ✅ | ✅ |
| PyInstaller binary | ✅ | ✅ | ✅ | curl new binary | ✅ |
| curl \| bash script | ✅ | ❌ | ✅ | re-run script | ✅ |
| snap / deb (current) | ✅ | ✅ | ❌ | snap refresh | requires store |

### Recommendation: two-tier distribution

#### Tier 1 — source install (Python users)

```bash
# pipx — most widely known
pipx install git+https://github.com/vs-slavchev/sharpshooter.git

# uv — faster, growing fast
uv tool install git+https://github.com/vs-slavchev/sharpshooter.git
```

Both create an isolated venv automatically, wire up the `sharpshooter` console
script to `~/.local/bin`, and support one-command upgrades (`pipx upgrade sharpshooter`
/ `uv tool upgrade sharpshooter`). No PyPI publishing needed.

#### Tier 2 — standalone binary (no Python needed)

Build with PyInstaller on GitHub Actions and attach the binary to each GitHub Release:

```yaml
# .github/workflows/release.yml
jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-22.04, macos-13]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install pyinstaller send2trash textual
      - run: pyinstaller --onefile sharpshooter/sharpshooter.py
      - uses: actions/upload-release-asset@v1
        with:
          asset_path: dist/sharpshooter
          asset_name: sharpshooter-${{ matrix.os }}-x86_64
```

User install (Linux):
```bash
curl -L https://github.com/vs-slavchev/sharpshooter/releases/latest/download/sharpshooter-linux-x86_64 \
     -o ~/.local/bin/sharpshooter && chmod +x ~/.local/bin/sharpshooter
```

User install (macOS):
```bash
curl -L https://github.com/vs-slavchev/sharpshooter/releases/latest/download/sharpshooter-macos-x86_64 \
     -o ~/.local/bin/sharpshooter && chmod +x ~/.local/bin/sharpshooter
```

#### Install script (optional convenience)

A minimal `install.sh` hosted alongside the site covers detection automatically:

```bash
#!/usr/bin/env bash
set -euo pipefail
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
BASE_URL="https://github.com/vs-slavchev/sharpshooter/releases/latest/download"
curl -fsSL "$BASE_URL/sharpshooter-${OS}-${ARCH}" -o ~/.local/bin/sharpshooter
chmod +x ~/.local/bin/sharpshooter
echo "Installed. Make sure ~/.local/bin is in your PATH."
```

Users run: `curl -fsSL https://yoursite.com/install.sh | bash`

---

## 5. Configuration

### Format recommendation: TOML

TOML beats the current INI (`configparser`) for this use case:

| | INI (current) | TOML |
|---|---|---|
| Comments | ✅ | ✅ |
| Nested tables | ❌ | ✅ |
| Arrays | ❌ (workarounds) | ✅ |
| Typed values | ❌ (strings only) | ✅ (bool, int, float, …) |
| Stdlib support | ✅ | ✅ Python 3.11+ (`tomllib`) |
| Writeable from stdlib | ✅ | ❌ (need `tomli-w` for write) |

`tomllib` is read-only in the stdlib. For writing (e.g. persisting `show_hidden`
toggle), either write the INI side-car for mutable runtime prefs and TOML for
static user config, or add `tomli-w` as a second small dependency.

**Practical alternative with zero new deps**: keep the config readable as TOML via
`tomllib` (stdlib), write mutable runtime state to a separate small JSON file
(also stdlib). One file the user edits by hand (TOML), one file the app manages
(JSON). Clear separation.

### Config file location

Follow XDG: `~/.config/sharpshooter/config.toml`  
Migrate from `~/.sharpshooter_config` on first run.

### Proposed schema

```toml
# ~/.config/sharpshooter/config.toml

[keys]
up           = "e"
down         = "n"
open_parent  = "k"
open_child   = "i"
quit         = "q"
open_terminal = "t"
open_file    = "\n"
toggle_hidden = "h"
delete       = "x"
new_folder   = "f"
rename       = "r"
copy         = "c"
paste        = "p"
cut          = "d"
zip_unzip    = "z"
mark_item    = "m"
undo         = "u"

[settings]
show_hidden    = false
confirm_delete = true   # prompt before deleting
sort_by        = "name" # name | size | date | extension
sort_reverse   = false

[theme]
# Named ANSI colors or hex strings (if the renderer supports 24-bit)
directory        = "blue"
executable       = "green"
symlink          = "cyan"
broken_symlink   = "red"
selected_fg      = "white"
selected_bg      = "blue"

[file_types]
# Override the default opener (xdg-open / open) per extension.
# Use $EDITOR, $PAGER, or any shell-visible command.
".pdf"  = "mupdf"
".mp4"  = "mpv"
".md"   = "$EDITOR"

[bookmarks]
# Press the bookmark key, then the letter to jump.
h = "~"
d = "~/Downloads"
p = "~/dev"

[[commands]]
# User-defined shell commands. {file} = selected path, {name} = basename, {dir} = cwd.
key         = "F5"
description = "compress to tar.gz"
command     = "tar -czf {name}.tar.gz {file}"

[[commands]]
key         = "F6"
description = "make executable"
command     = "chmod +x {file}"
```

### Config manager rewrite sketch

```python
# config_manager.py
import tomllib          # Python 3.11+; or: import tomli as tomllib
import json
from pathlib import Path

CONFIG_PATH  = Path.home() / ".config" / "sharpshooter" / "config.toml"
RUNTIME_PATH = Path.home() / ".config" / "sharpshooter" / "runtime.json"
DEFAULTS = { ... }  # mirror the schema above

def load_config() -> dict:
    if not CONFIG_PATH.exists():
        _write_default_config()
    with open(CONFIG_PATH, "rb") as f:
        user = tomllib.load(f)
    return _deep_merge(DEFAULTS, user)

def load_runtime() -> dict:
    if RUNTIME_PATH.exists():
        return json.loads(RUNTIME_PATH.read_text())
    return {}

def save_runtime(data: dict):
    RUNTIME_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_PATH.write_text(json.dumps(data, indent=2))
```

### How other file managers handle config (reference)

| Manager | Format | Notable pattern |
|---------|--------|-----------------|
| **Ranger** | Plain text + Python | Separate files: `rc.conf`, `rifle.conf` (openers), `commands.py` |
| **lf** | Plain text (`lfrc`) | Shell commands inline; simple `set`/`map`/`cmd` DSL |
| **Yazi** | TOML | Three files: `yazi.toml`, `keymap.toml`, `theme.toml` |
| **nnn** | Env vars only | No config file at all; plugins are standalone scripts |

Yazi's split into three focused files is clean; for Sharpshooter's scale a single
`config.toml` is appropriate until the feature set warrants splitting.

---

## 6. Dependency budget (proposed)

| Package | Why | Size |
|---------|-----|------|
| `send2trash` | Cross-platform native trash | ~20 KB |
| `textual` | Modern TUI renderer (Phase 2+) | ~10 MB with deps |
| `tomli-w` | Write TOML (only if not using JSON for runtime state) | ~10 KB |

`send2trash` is the only addition needed for Phase 1 cross-platform work.
`textual` comes in Phase 2 when the renderer is refactored.
`tomli-w` is optional — the JSON runtime state approach avoids it entirely.

---

## 7. Suggested implementation order

1. **Cross-platform actions** — `platform_utils.py`, rewrite terminal/file-open/trash in
   `file_system.py`, add `send2trash`. Low risk, high value, no architecture change.
2. **Config migration** — `~/.sharpshooter_config` → `~/.config/sharpshooter/config.toml`;
   add bookmarks, `file_types`, `commands` sections. Medium effort, self-contained.
3. **Distribution** — GitHub Actions release workflow for PyInstaller binaries;
   update README with pipx / uv / binary install instructions.
4. **Renderer refactor** — introduce `Renderer` interface, then `TextualRenderer`.
   Largest effort; do last once the above improvements are stable.
