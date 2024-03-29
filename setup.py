#!/usr/bin/env python3

from setuptools import setup

setup(
    name='sharpshooter',
    version='1.3.10',
	description='minimal terminal application that in a single key press lets you navigate and copy/cut/delete/archive your files and open the terminal',
	author='Veselin Slavchev',
	author_email='vs_slavchev@abv.bg',
	license='GNU',
	url='https://github.com/vs-slavchev/sharpshooter',
    py_modules=['sharpshooter', 'controller', 'content', 'config_manager', 'cursed_files_pane', 'fs_item', 'input_keys', 'pane_manager', 'file_system', 'utility', 'single_line_window', 'file_system_error'],
    install_requires=[],
    entry_points='''
        [console_scripts]
        sharpshooter=sharpshooter:main
    ''',
)
