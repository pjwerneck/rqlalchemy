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


with open('flask_rql/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

install = [
    'pyrql',
    'sqlalchemy',
    'werkzeug',
    'flask',
    ]

setup(
    name='flask-rql',
    version=version,
    description='Resource Query Language for Flask',
    packages=['flask_rql'],
    tests_require=['pytest'],
    install_requires=install,
    )
