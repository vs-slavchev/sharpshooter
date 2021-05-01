from setuptools import setup

setup(
    name='sharpshooter',
    py_modules=['sharpshooter'],
    install_requires=[],
    entry_points='''
        [console_scripts]
        sharpshooter=sharpshooter:main
    ''',
)
