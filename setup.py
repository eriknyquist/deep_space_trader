import os
from setuptools import setup

from deep_space_trader import __version__ as version

HERE = os.path.abspath(os.path.dirname(__file__))
README = os.path.join(HERE, "README.rst")
REQFILE = 'requirements.txt'

classifiers = [
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
]

# Where the README's images are on GitHub. The README links to them by their
# path in the project (e.g. images/store.png), which works on GitHub and for the
# PDF manual, but not on PyPI, which only has the text: there they need full addresses
IMAGES_URL = 'https://raw.githubusercontent.com/eriknyquist/deep_space_trader/master/images/'

# (UTF-8, or Windows would read it in its own encoding and garble characters like "×")
with open(README, 'r', encoding='utf-8') as f:
    long_description = f.read().replace('.. image:: images/', '.. image:: ' + IMAGES_URL)

with open(REQFILE, 'r') as fh:
    dependencies = fh.readlines()

setup(
    name='deep_space_trader',
    version=version,
    description=('A turn-based strategy game. You are the owner & operator of a '
                 'deep-space commercial trading vessel willing to do anything to get rich.'),
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='http://github.com/eriknyquist/deep_space_trader',
    author='Erik Nyquist',
    author_email='eknyquist@gmail.com',
    license='MIT',
    classifiers=classifiers,
    install_requires=dependencies,
    packages=['deep_space_trader'],
    package_data={'deep_space_trader':['images/*', 'audio/*', 'translations/*.qm']},
    include_package_data=True,
    zip_safe=False
)
