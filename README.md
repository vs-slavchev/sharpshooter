
# Sharpshooter ![LOGO](./img/sharpshooter_logo.svg) [![sharpshooter](https://snapcraft.io/sharpshooter/badge.svg)](https://snapcraft.io/sharpshooter) [![Build Status](https://travis-ci.com/vs-slavchev/sharpshooter.svg?branch=master)](https://travis-ci.com/vs-slavchev/sharpshooter)

Minimal file manager in the terminal.

Single-key hotkeys for easy workflow.

Simple to configure and hack at.
![LOC counter](https://tokei.rs/b1/github/vs-slavchev/sharpshooter?category=code)

*What this is not: complex, with many features, with thousands of commits, hard to get into, promising support for special encodings or alphabets, supporting extra features like bulk rename.*

# Single key actions
- [x] open terminal at current folder
- [x] archive/extract
- [x] make new folder
- [x] toggle hidden files visibility
- [x] rename
- [x] delete
- [x] undo delete
- [x] copy/cut
- [x] open file

## Features
- [x] select multiple files
- [x] configurable hotkeys

# Install and remove
`snap install --beta sharpshooter --devmode`

`snap remove sharpshooter`

or download the latest .deb from the releases.

### Change hotkeys

- edit the `.sharpshooter_config` in your home dir with your preferred hotkeys

# Technologies

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

[curses](https://docs.python.org/3/library/curses.html)

[pathlib](https://docs.python.org/3/library/pathlib.html)

[configparser](https://docs.python.org/3/library/configparser.html)

[shutil](https://docs.python.org/3/library/shutil.html)

[logging](https://docs.python.org/3/library/logging.html)

# Block diagram
![block_diagram](./docs/block_diagram.svg)

# Releasing as .deb
1. install ```sudo apt-get install build-essential devscripts debhelper debmake dh-python python3-all```
2. ```python3 setup.py sdist```
3. ```mv dist/sharpshooter-*.tar.gz .```
4. ```tar -xzmf sharpshooter-*.tar.gz```
5. cd into sharpshooter-* folder
6. ```debmake -b":python3"```
7. ```debuild```

# Running in IntelliJ
- add `PYTHONUNBUFFERED=1` as env variable
- check Emulate terminal in output console

# Inspired by
[ranger](https://ranger.github.io/)

[Midnight Comander](https://midnight-commander.org/)
