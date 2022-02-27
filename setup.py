import unittest
import os
import sys
from setuptools import setup, find_packages
from distutils.core import Command

from deep_space_trader import __version__ as version

HERE = os.path.abspath(os.path.dirname(__file__))
README = os.path.join(HERE, "README.rst")
REQFILE = 'requirements.txt'

classifiers = [
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
]

with open(README, 'r') as f:
    long_description = f.read()

with open(REQFILE, 'r') as fh:
    dependencies = fh.readlines()

setup(
    name='deep_space_trader',
    version=version,
    description=('Dumb space game'),
    long_description=long_description,
    url='http://github.com/eriknyquist/deep_space_trader',
    author='Erik Nyquist',
    author_email='eknyquist@gmail.com',
    license='Apache 2.0',
    install_requires=dependencies,
    packages=['deep_space_trader'],
    package_data={'deep_space_trader':['images/*']},
    include_package_data=True,
    zip_safe=False
)
