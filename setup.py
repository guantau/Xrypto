#!/usr/bin/env python

from setuptools import setup, find_packages
import sys


if sys.version_info < (3,):
    print("xrypto requires Python version >= 3.0")
    sys.exit(1)

packages = find_packages(where='.', exclude=["*.tests", "*.tests.*", "tests.*", "tests"])

setup(name='xrypto',
      packages = packages,
      version='0.3',
      description='opportunity detector and automated trading',
      author='Phil Song',
      author_email='songbohr@gmail.com',
      url='https://github.com/philsong/xrypto',
      test_suite='nose.collector',
      tests_require=['nose'],
  )
