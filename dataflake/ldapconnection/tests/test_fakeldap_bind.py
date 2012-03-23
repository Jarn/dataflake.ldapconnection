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

$Id$
"""

import doctest
import unittest

from dataflake.ldapconnection.tests.base import FakeLDAPTests
from dataflake.ldapconnection.tests.base import fakeldap

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

    def test_unbind_clears_last_bind(self):
        conn = self._makeOne()
        user_dn, password = self._addUser('foo')

        self.failUnless(conn.simple_bind_s(user_dn, password))
        self.assertEquals(conn._last_bind[1], (user_dn, password))

        conn.unbind_s()
        self.assertEquals(conn._last_bind, None)


class HashedPasswordTests(FakeLDAPTests):

    def test_connection_is_hashed(self):
        conn = self._makeOne()
        self.assertEquals(conn.hash_password, True)

    def test_password_is_hashed(self):
        conn = self._makeOne()
        self._addUser('foo')

        res = conn.search_s( 'ou=users,dc=localhost'
                           , query='(cn=foo)'
                           )
        pwd = res[0][1]['userPassword'][0]
        self.assertEquals(pwd, fakeldap.hash_pwd('foo_secret'))

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


class ClearTextPasswordTests(FakeLDAPTests):

    def _getTargetClass(self):
        from dataflake.ldapconnection.tests.fakeldap import FakeLDAPConnection

        class ClearTextConnection(FakeLDAPConnection):
            """ A FakeLDAPConnection with password hashing disabled
            """
            hash_password = False

        return ClearTextConnection

    def test_connection_is_clear_text(self):
        conn = self._makeOne()
        self.assertEquals(conn.hash_password, False)

    def test_password_is_clear_text(self):
        conn = self._makeOne()
        user_dn, password = self._addUser('foo')

        res = conn.search_s( 'ou=users,dc=localhost'
                           , query='(cn=foo)'
                           )
        pwd = res[0][1]['userPassword'][0]
        self.assertEquals(pwd, 'foo_secret')

    def test_bind_success(self):
        conn = self._makeOne()
        user_dn, password = self._addUser('foo')

        # Login with correct credentials
        self.assertEquals(user_dn, 'cn=foo,ou=users,dc=localhost')
        self.assertEquals(password, 'foo_secret')
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


def test_suite():
    import sys
    return unittest.findTestCases(sys.modules[__name__])
