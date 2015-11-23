# -*- coding:utf-8 -*-

import os
import sys


from setuptools import setup, find_packages
here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.rst')) as f:
        README = f.read()
    with open(os.path.join(here, 'CHANGES.txt')) as f:
        CHANGES = f.read()
except IOError:
    README = CHANGES = ''


install_requires = [
]


docs_extras = [
]

tests_require = [
]

testing_extras = tests_require + [
]

setup(name='dictremapper',
      version='0.0.2',
      description='remapping dict',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: Implementation :: CPython",
      ],
      keywords='dict, remapping, structure',
      author="podhmo",
      author_email="",
      url="https://github.com/podhmo/dictremapper",
      packages=find_packages(exclude=["dictremapper.tests", "demo"]),
      license="mit",
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      extras_require={
          'testing': testing_extras,
          'docs': docs_extras,
      },
      tests_require=tests_require,
      test_suite="dictremapper.tests",
      entry_points="""
""")
