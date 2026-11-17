"""
    Knows which platform we run on and which external commands to try, in priority order, for OS-specific actions.
    Every function here only builds candidate lists; launching them is done by file_system.
"""
import functools
import os
import shlex
import sys


def platform_type():
    """Returns 'macos' or 'linux'. WSL counts as Linux; use is_wsl() to add Windows-side fallbacks."""
    return 'macos' if sys.platform == 'darwin' else 'linux'


@functools.lru_cache(maxsize=None)
def is_wsl():
    try:
        with open('/proc/version') as f:
            return 'microsoft' in f.read().lower()
    except OSError:
        return False


def desktop_environment():
    return os.getenv('XDG_CURRENT_DESKTOP', '').lower()


def terminal_candidates(directory):
    """Return a priority-ordered list of argv lists for opening a terminal at directory.
    Every candidate is also launched with cwd=directory, so terminals without a working-dir flag still work."""
    candidates = []

    # the user's explicit choice always wins
    user_terminal = os.getenv('TERMINAL', '').strip()
    if user_terminal:
        try:
            candidates.append(shlex.split(user_terminal))
        except ValueError:
            pass

    if platform_type() == 'macos':
        if 'iterm' in os.getenv('TERM_PROGRAM', '').lower():
            candidates.append(['open', '-a', 'iTerm', directory])
        candidates.append(['open', '-a', 'Terminal', directory])
        return candidates

    if is_wsl():
        # a Linux path means nothing to Windows: ask Windows Terminal for a WSL shell that cds there
        wsl_shell = ['wsl.exe']
        if os.getenv('WSL_DISTRO_NAME'):  # the distro we run in, not the default one
            wsl_shell += ['-d', os.environ['WSL_DISTRO_NAME']]
        # wt.exe splits its command line at ';' unless it is escaped
        candidates.append(['wt.exe'] + wsl_shell + ['--cd', directory.replace(';', '\\;')])

    linux_terminals = [
        # the system's configured default terminal comes before any particular one
        ['exo-open', '--working-directory', directory, '--launch', 'TerminalEmulator'],
        ['x-terminal-emulator', '--working-directory', directory],
        ['gnome-terminal', '--working-directory', directory],
        ['konsole', '--workdir', directory],
        ['xfce4-terminal', '--working-directory', directory],
        ['kitty', '--directory', directory],
        ['alacritty', '--working-directory', directory],
        ['wezterm', 'start', '--cwd', directory],
        ['foot', '--working-directory', directory],
        ['urxvt', '-cd', directory],
        ['xterm'],
    ]
    # the desktop's own terminal goes first, the rest keep their order (sort is stable)
    native = _native_terminal()
    linux_terminals.sort(key=lambda cmd: cmd[0] != native)
    return candidates + linux_terminals


def _native_terminal():
    de = desktop_environment()
    if 'gnome' in de or 'unity' in de:
        return 'gnome-terminal'
    if 'kde' in de:
        return 'konsole'
    if 'xfce' in de:
        return 'xfce4-terminal'
    return None


def open_file_candidates(path):
    """Return a priority-ordered list of argv lists for opening path with the default GUI application.
    Terminal programs such as $EDITOR are deliberately not used: they would fight curses for the screen."""
    if platform_type() == 'macos':
        return [['open', path]]
    candidates = []
    if is_wsl():
        candidates.append(['wslview', path])
    candidates += [
        ['xdg-open', path],
        ['gio', 'open', path],
        ['kde-open', path],
        ['exo-open', path],
    ]
    return candidates


def clipboard_candidates():
    """Return a priority-ordered list of argv lists that copy their stdin to the system clipboard."""
    if platform_type() == 'macos':
        return [['pbcopy']]

    wayland = [['wl-copy']]
    x11 = [['xclip', '-selection', 'clipboard'], ['xsel', '--clipboard', '--input']]

    candidates = []
    if is_wsl():
        candidates.append(['clip.exe'])
    if os.getenv('WAYLAND_DISPLAY'):
        candidates += wayland + x11  # XWayland usually makes X11 tools work too
    else:
        candidates += x11 + wayland
    return candidates


def stdin_encoding(cmd):
    """clip.exe reads its input as UTF-16 (with a byte order mark); everything else here takes UTF-8."""
    return 'utf-16' if cmd and cmd[0] == 'clip.exe' else 'utf-8'


def clipboard_install_hint():
    if platform_type() == 'macos':
        return "Check that pbcopy works in this terminal"
    if is_wsl():
        return "Check that clip.exe is reachable, or install wl-clipboard, xclip or xsel"
    return "Install wl-clipboard, xclip or xsel"


def open_file_install_hint():
    if platform_type() == 'macos':
        return "No default application is set for it"
    if is_wsl():
        return "Install wslu or xdg-utils"
    return "Install xdg-utils"
