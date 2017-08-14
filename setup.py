# ********************************************************************************
# * Project: Eskapade - A python-based package for data analysis                 *
# * Created: 2017/08/08                                                          *
# * Description:                                                                 *
# *     Statistics functionality for data-quality                                *
# *                                                                              *
# * Authors:                                                                     *
# *      KPMG Big Data team, Amstelveen, The Netherlands                         *
# *                                                                              *
# * Redistribution and use in source and binary forms, with or without           *
# * modification, are permitted according to the terms listed in the file        *
# * LICENSE.                                                                     *
# ********************************************************************************

import sys
import logging

from setuptools import setup
from setuptools import find_packages
from setuptools.command.test import test as TestCommand

NAME = 'Eskapade'

MAJOR = 0
REVISION = 6
PATCH = 0
DEV = True

VERSION = '{major}.{revision}.{patch}'.format(major=MAJOR, revision=REVISION, patch=PATCH)
FULL_VERSION = VERSION
if DEV:
    FULL_VERSION += '.dev'

CMDCLASS = dict()
COMMAND_OPTIONS = dict()

logging.basicConfig()
logger = logging.getLogger(__file__)


def write_version_py(filename: str = 'python/eskapade/version.py') -> None:
    """
    Write package version to version.py. This will ensure that
    the version in version.py is in sync with us.

    :param filename: The version.py to write too.
    :type filename: str
    :return:
    :rtype: None
    """

    # Do not modify the indentation of version_str!
    version_str = """
# THIS IS FILE IS AUTO-GENERATED BY ESKAPADE SETUP.PY!
    
version = '{version!s}'
full_version = '{full_version!s}'
release = {is_release!s}
"""

    version_file = open(filename, 'w')
    try:
        version_file.write(version_str.format(version=VERSION,
                                              full_version=FULL_VERSION,
                                              is_release=not DEV))
    finally:
        version_file.close()


def exclude_packages() -> list:
    """
    Determine which packages we would like to install. This depends on whether certain dependencies
    are available or not.

    TODO: Probably need to rethink this.

    :return: A list of packages to exclude.
    :rtype: list
    """
    # Tests are excluded by default.
    exclude = ['*tests*']

    try:
        import ROOT
        import RooFit
        import RooStats
    except ImportError:
        logger.fatal('PyROOT and RooFit are missing! Not going to install ROOT analysis modules!')
        # This does not really work. Tests are excluded though.
        exclude.append('*root_analysis*')

    return exclude


# This is for auto-generating documentation.
# One can generate documentation by executing:
# python setup.py build_sphinx -i
HAVE_SPHINX = True
try:
    from sphinx.setup_command import BuildDoc

    cmd_string = 'build_sphinx'

    CMDCLASS[cmd_string] = BuildDoc
    COMMAND_OPTIONS[cmd_string] = {
        'project': ('setup.py', NAME),
        'version': ('setup.py', VERSION),
        'release': ('setup.py', FULL_VERSION)
    }
except ImportError:
    logger.fatal('Missing Sphinx packages!')
    HAVE_SPHINX = False


class PyTest(TestCommand):
    """
    A pytest runner helper.
    """

    user_options = [('pytest-args=', 'a', 'Arguments to pass to pytest')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def run_tests(self):
        import shlex
        # We only install this when needed.
        import pytest
        print(self.pytest_args)
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


CMDCLASS['test'] = PyTest


def setup_package() -> None:
    """
    The main setup method. It is responsible for setting up and installing the package.

    It also provides commands for generating docs and running tests.

    To generate sphinx docs execute:

    >>> python setup.py build_sphinx -i

    in the project folder.

    To run tests execute:

    >>> python setup test -a "some pytest test arguments"

    in the project folder.

    :return:
    :rtype: None
    """
    write_version_py()

    setup(name=NAME,
          version=VERSION,
          url='http://eskapade.kave.io',
          license='',
          author='KPMG',
          description='Eskapade modular analytics',
          python_requires='>=3.5',
          package_dir={'': 'python'},
          packages=find_packages(where='python', exclude=exclude_packages()),
          include_package_data=True,
          package_data={
              NAME.lower(): ['templates/*']
          },
          install_requires=[
              'numba==0.34.0',
              'jupyter==1.0.0',
              'matplotlib==2.0.2',
              'numpy==1.13.1',
              'scipy==0.19.1',
              'statsmodels==0.8.0',
              'pandas==0.20.3',
              'tabulate==0.7.7',
              'sortedcontainers==1.5.7',
              'histogrammar==1.0.8',
              'names==0.3.0',
              'fastnumbers==2.0.1',
              'root_numpy==4.7.3'
          ],
          tests_require=['pytest'],
          cmdclass=CMDCLASS,
          command_options=COMMAND_OPTIONS,
          # The following 'creates' executable scripts for *nix and Windows.
          # As an added the bonus the Windows scripts will auto-magically
          # get a .exe extension.
          #
          # eskapade: main/app application entry point.
          # eskapade_trial: test entry point.
          entry_points={
              'console_scripts': [
                  'eskapade_ignite = eskapade.entry_points:eskapade_ignite',
                  'eskapade_run = eskapade.entry_points:eskapade_run',
                  'eskapade_trial = eskapade.entry_points:eskapade_trial'
              ]
          }
          )


if __name__ == '__main__':
    setup_package()
