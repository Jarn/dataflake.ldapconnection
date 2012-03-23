##############################################################################
#
# Copyright (c) 2008-2009 Jens Vagelpohl and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

__version__ = '1.3dev'

import os

from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

_boundary = '\n' + ('-' * 60) + '\n\n'

setup(name='dataflake.ldapconnection',
      version=__version__,
      description='LDAP connection library',
      long_description=( read('README.txt') 
                       + "\n\nDownload\n========"
                       ),
      classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration :: Authentication/Directory :: LDAP",
        ],
      keywords='ldap ldapv3',
      author="Agendaless Consulting and Jens Vagelpohl",
      author_email="jens@dataflake.org",
      url="http://pypi.python.org/pypi/dataflake.ldapconnection",
      license="ZPL 2.1",
      packages=find_packages(),
      include_package_data=True,
      namespace_packages=['dataflake'],
      zip_safe=False,
      setup_requires=['setuptools-git'],
      tests_require = [
              'python-ldap>=2.3.0',
              'dataflake.cache',
              ],
      install_requires=[
              'setuptools',
              'python-ldap>=2.3.0',
              'zope.interface',
              'dataflake.cache',
              ],
      test_suite='dataflake.ldapconnection.tests',
      )

