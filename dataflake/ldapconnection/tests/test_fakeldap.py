##############################################################################
#
# Copyright (c) 2008-2010 Jens Vagelpohl and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" test_fakeldap: Tests for the FakeLDAP testing fixture

$Id: test_fakeldap.py 1901 2010-02-07 19:01:08Z jens $
"""

import doctest
import unittest

from dataflake.ldapconnection.tests.base import FakeLDAPTests


class FakeLDAPBasicTests(FakeLDAPTests):

    def test_defaults(self):
        conn = self._makeOne()
        self.failIf(conn.start_tls_called)
        self.failIf(conn.args)
        self.failIf(conn.kwargs)
        self.failIf(conn.options)
        self.failIf(conn._last_bind)

    def test_saving_args(self):
        conn = self._makeOne('arg1', 'arg2', arg3='foo', arg4='bar')
        self.assertEquals(conn.args, ('arg1', 'arg2'))
        self.assertEquals(conn.kwargs, {'arg3':'foo', 'arg4':'bar'})

    def test_set_option(self):
        conn = self._makeOne()
        conn.set_option('foo', 'bar')
        conn.set_option(1, 2)
        self.assertEquals(conn.options, {'foo':'bar', 1:2})

    def test_start_tls(self):
        conn = self._makeOne()
        conn.start_tls_s()
        self.failUnless(conn.start_tls_called)

    def test_result(self):
        conn = self._makeOne()
        self.assertEquals( conn.result()
                         , ( 'partial'
                           , [('partial result', {'dn': 'partial result'})]
                           )
                         )


def test_suite():
    from dataflake.ldapconnection.tests import fakeldap
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FakeLDAPBasicTests))
    suite.addTest(doctest.DocTestSuite(fakeldap))
    return suite

