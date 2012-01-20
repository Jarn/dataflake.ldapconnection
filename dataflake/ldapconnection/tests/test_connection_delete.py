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
""" test_connection_delete: Tests for the LDAPConnection delete method

$Id: test_connection_delete.py 1901 2010-02-07 19:01:08Z jens $
"""

import unittest

from dataflake.ldapconnection.tests.base import LDAPConnectionTests
from dataflake.ldapconnection.tests.dummy import ISO_8859_1_ENCODED
from dataflake.ldapconnection.tests.dummy import ISO_8859_1_UTF8

class ConnectionDeleteTests(LDAPConnectionTests):

    def test_delete_noauthentication(self):
        self._addRecord('cn=foo,dc=localhost')
        conn = self._makeSimple()
        conn.delete('cn=foo,dc=localhost')
        connection = conn._getConnection()
        binduid, bindpwd = connection._last_bind[1]
        self.assertEqual(binduid, u'')
        self.assertEqual(bindpwd, '')

    def test_delete_authentication(self):
        self._addRecord('cn=foo,dc=localhost')
        conn = self._makeSimple()
        bind_dn_apiencoded = 'cn=%s,dc=localhost' % ISO_8859_1_ENCODED
        bind_dn_serverencoded = 'cn=%s,dc=localhost' % ISO_8859_1_UTF8
        self._addRecord(bind_dn_serverencoded, userPassword='foo')
        conn.delete( 'cn=foo,dc=localhost'
                   , bind_dn=bind_dn_apiencoded
                   , bind_pwd='foo'
                   )
        connection = conn._getConnection()
        binduid, bindpwd = connection._last_bind[1]
        self.assertEqual(binduid, bind_dn_serverencoded)
        self.assertEqual(bindpwd, 'foo')

    def test_delete(self):
        self._addRecord('cn=foo,dc=localhost')
        conn = self._makeSimple()
        results = conn.search('dc=localhost', '(cn=foo)')
        self.assertEquals(results['results'], [{'dn': 'cn=foo'}])

        conn.delete('cn=foo,dc=localhost')
        results = conn.search('dc=localhost', '(cn=foo)')
        self.failIf(results['results'])

    def test_delete_readonly(self):
        conn = self._makeOne('host', 636, 'ldap', self._factory, read_only=True)
        self.assertRaises(RuntimeError, conn.delete, 'cn=foo')

    def test_delete_referral(self):
        import ldap
        self._addRecord('cn=foo,dc=localhost')
        exc_arg = {'info':'please go to ldap://otherhost:1389'}
        conn, ldap_connection = self._makeRaising( 'delete_s'
                                                 , ldap.REFERRAL
                                                 , exc_arg
                                                 )
        conn.delete('cn=foo,dc=localhost')
        self.assertEqual(ldap_connection.conn_string, 'ldap://otherhost:1389')
        self.assertEquals(ldap_connection.args, ('cn=foo,dc=localhost',))


def test_suite():
    import sys
    return unittest.findTestCases(sys.modules[__name__])

