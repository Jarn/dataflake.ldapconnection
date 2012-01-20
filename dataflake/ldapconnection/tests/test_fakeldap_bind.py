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
""" test_fakeldap_bind: Tests for the FakeLDAP simple_bind_s method

$Id: test_fakeldap_bind.py 1901 2010-02-07 19:01:08Z jens $
"""

import base64
import doctest
import unittest

from dataflake.ldapconnection.tests.base import FakeLDAPTests

class FakeLDAPBindTests(FakeLDAPTests):

    def test_bind_empty_pwd(self):
        conn = self._makeOne()

        # special case for empty password (???)
        self.failUnless(conn.simple_bind_s('cn=Anybody', ''))
        self.assertEquals(conn._last_bind[1], ('cn=Anybody', ''))

    def test_bind_manager(self):
        conn = self._makeOne()

        # special case for logging in as "Manager"
        self.failUnless(conn.simple_bind_s('cn=Manager', 'whatever'))
        self.assertEquals(conn._last_bind[1], ('cn=Manager', 'whatever'))

    def test_bind_success(self):
        conn = self._makeOne()
        user_dn, password = self._addUser('foo')

        # Login with correct credentials
        self.failUnless(conn.simple_bind_s(user_dn, password))
        self.assertEquals(conn._last_bind[1], (user_dn, password))

    def test_bind_wrong_pwd(self):
        import ldap
        conn = self._makeOne()
        user_dn, password = self._addUser('foo')

        # Login with bad credentials
        self.assertRaises( ldap.INVALID_CREDENTIALS
                         , conn.simple_bind_s
                         , user_dn
                         , 'INVALID PASSWORD'
                         )

    def test_bind_no_password_in_record(self):
        import ldap
        conn = self._makeOne()


        # Users with empty passwords cannot log in
        user2 = [('cn', ['user2'])]
        conn.add_s('cn=user2,ou=users,dc=localhost', user2)
        self.assertRaises( ldap.INVALID_CREDENTIALS
                         , conn.simple_bind_s
                         , 'cn=user2,ou=users,dc=localhost'
                         , 'ANY PASSWORD'
                         )


def test_suite():
    import sys
    return unittest.findTestCases(sys.modules[__name__])
