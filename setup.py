#!/usr/bin/env python

from distutils.core import setup

setup(
    name='ppo',
    version='0.1.1',
    description='Parses Pentesting tools output',
    author='Matt Haggard',
    author_email='haggardii@gmail.com',
    url='https://github.com/iffy/ppo',
    packages=[
        'ppo', 'ppo.test',
    ],
    install_requires=[
        'yaml',
        'lxml',
        'importlib',
    ],
    scripts=[
        'scripts/ppo',
    ]
)