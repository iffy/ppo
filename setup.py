#!/usr/bin/env python
# Copyright (c) The ppo team
# See LICENSE for details.


from distutils.core import setup

setup(
    name='ppo',
    version='0.3.1',
    description='Parses Pentesting tools output',
    author='Matt Haggard',
    author_email='haggardii@gmail.com',
    url='https://github.com/iffy/ppo',
    packages=[
        'ppo', 'ppo.test',
        'ppo.parse_plugins',
    ],
    install_requires=[
        'PyYaml',
        'lxml',
        'importlib',
        'structlog',
        'ordereddict',
    ],
    scripts=[
        'scripts/ppo',
    ]
)