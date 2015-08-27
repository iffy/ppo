#!/usr/bin/env python

from distutils.core import setup

setup(
    name='ppo',
    version='0.1.0',
    description='Parses Pentesting tools output',
    author='Matt Haggard',
    author_email='haggardii@gmail.com',
    url='https://github.com/iffy/ppo',
    packages=[
        'ppo', 'ppo.test',
    ],
    scripts=[
        'scripts/ppo',
    ]
)