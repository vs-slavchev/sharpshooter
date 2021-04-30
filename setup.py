from setuptools import setup

setup(
    name='sharpshooter',
    py_modules=['sharpshooter'],
    version='0.9.0',
    install_requires=[],
    entry_points='''
        [console_scripts]
        sharpshooter=sharpshooter:main
    ''',
)
