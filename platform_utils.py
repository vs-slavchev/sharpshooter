import os
import sys
import shutil


def platform_type():
    """Returns 'macos' or 'linux'."""
    if sys.platform == 'darwin':
        return 'macos'
    return 'linux'


def desktop_environment():
    return os.getenv('XDG_CURRENT_DESKTOP', '').lower()


def terminal_candidates(directory):
    """Return a priority-ordered list of argv lists for opening a terminal at directory."""
    if platform_type() == 'macos':
        candidates = []
        if 'iterm' in os.getenv('TERM_PROGRAM', '').lower():
            candidates.append(['open', '-a', 'iTerm', directory])
        candidates.append(['open', '-a', 'Terminal', directory])
        return candidates

    de = desktop_environment()
    candidates = []

    # DE-native terminal first (only if actually installed)
    if ('gnome' in de or 'unity' in de) and shutil.which('gnome-terminal'):
        candidates.append(['gnome-terminal', '--working-directory', directory])
    elif 'kde' in de and shutil.which('konsole'):
        candidates.append(['konsole', '--workdir', directory])
    elif 'xfce' in de and shutil.which('xfce4-terminal'):
        candidates.append(['xfce4-terminal', '--working-directory', directory])

    # Generic launchers and modern terminals as ordered fallback
    for exe, cmd in [
        ('exo-open',          ['exo-open', '--working-directory', directory, '--launch', 'TerminalEmulator']),
        ('x-terminal-emulator', ['x-terminal-emulator', '--working-directory', directory]),
        ('kitty',             ['kitty', '--directory', directory]),
        ('alacritty',         ['alacritty', '--working-directory', directory]),
        ('wezterm',           ['wezterm', 'start', '--cwd', directory]),
        ('urxvt',             ['urxvt', '-cd', directory]),
        ('xterm',             ['xterm']),   # no working-dir flag; caller passes cwd=
    ]:
        if shutil.which(exe):
            candidates.append(cmd)

    return candidates
