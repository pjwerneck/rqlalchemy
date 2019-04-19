# -*- coding: utf-8 -*-

import os
import re
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'test':
    try:
        __import__('pytest')
    except ImportError:
        print('pytest required.')
        sys.exit(1)

    errors = os.system('pytest')
    sys.exit(bool(errors))


with open('rqlalchemy/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

install = [
    'pyrql',
    'sqlalchemy',
]

setup(
    name='rqlalchemy',
    version=version,
    description='Resource Query Language for SQLAlchemy',
    packages=['rqlalchemy'],
    tests_require=['pytest'],
    install_requires=install,
)
