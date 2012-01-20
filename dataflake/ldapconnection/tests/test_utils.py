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
""" test_utils: Tests for the utils utility functions

$Id: test_utils.py 1874 2010-01-26 11:55:18Z jens $
"""

import unittest

from dataflake.ldapconnection.utils import escape_dn

class UtilsTest(unittest.TestCase):

    def test_escape_dn(self):
        # http://www.dataflake.org/tracker/issue_00623
        dn = 'cn="Joe Miller, Sr.", ou="odds+sods <1>", dc="host;new"'
        dn_clean = 'cn=Joe Miller\\, Sr.,ou=odds\\+sods \\<1\\>,dc=host\\;new'
        self.assertEquals(escape_dn(dn), dn_clean)

        self.assertEquals(escape_dn(None), None)


def test_suite():
    import sys
    return unittest.findTestCases(sys.modules[__name__])

