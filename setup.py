#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

import os.path
import sys

sys.path.insert(0, os.path.abspath('.'))
from exopy_pulses.version import __version__

PROJECT_NAME = 'exopy_i3py'


def long_description():
    """Read the project description from the README file.

    """
    with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
        return f.read()


setup(
    name=PROJECT_NAME,
    description='ExopyI3py plugin package',
    version=__version__,
    long_description=long_description(),
    author='see AUTHORS',
    author_email='m.dartiailh@gmail.com',
    url='https://github.com/exopy/exopy_i3py',
    download_url='https://github.com/exopy/exopy_i3py/tarball/master',
    keywords='experiment automation GUI',
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Physics',
        'Programming Language :: Python :: 3.6'
        ],
    zip_safe=False,
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={'': ['*.enaml']},
    requires=['exopy', 'i3py'],
    install_requires=['exopy', 'i3py'],
    entry_points={
        'exopy_package_extension':
        'exopy_i3py = %s:list_manifests' % PROJECT_NAME}
)
