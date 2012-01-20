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
""" test_connection_insert: Tests for the LDAPConnection insert method

$Id: test_connection_insert.py 1897 2010-02-06 13:27:07Z jens $
"""

import unittest

from dataflake.ldapconnection.tests.base import LDAPConnectionTests
from dataflake.ldapconnection.tests.dummy import ISO_8859_1_ENCODED
from dataflake.ldapconnection.tests.dummy import ISO_8859_1_UTF8

class ConnectionInsertTests(LDAPConnectionTests):

    def test_insert_noauthentication(self):
        conn = self._makeSimple()
        conn.insert('dc=localhost', 'cn=jens', attrs={})
        connection = conn._getConnection()
        binduid, bindpwd = connection._last_bind[1]
        self.assertEqual(binduid, '')
        self.assertEqual(bindpwd, '')

    def test_insert_authentication(self):
        conn = self._makeSimple()
        bind_dn_apiencoded = 'cn=%s,dc=localhost' % ISO_8859_1_ENCODED
        bind_dn_serverencoded = 'cn=%s,dc=localhost' % ISO_8859_1_UTF8
        self._addRecord(bind_dn_serverencoded, userPassword='foo')
        conn.insert( 'dc=localhost'
                   , 'cn=jens'
                   , attrs={}
                   , bind_dn=bind_dn_apiencoded
                   , bind_pwd='foo'
                   )
        connection = conn._getConnection()
        binduid, bindpwd = connection._last_bind[1]
        self.assertEqual(binduid, bind_dn_serverencoded)
        self.assertEqual(bindpwd, 'foo')

    def test_insert(self):
        attributes = { 'cn' : 'jens'
                     , 'multivaluestring' : 'val1;val2;val3'
                     , 'multivaluelist' : ['val1', 'val2']
                     }
        conn = self._makeSimple()
        conn.insert('dc=localhost', 'cn=jens', attrs=attributes)

        results = conn.search('dc=localhost', fltr='(cn=jens)')
        self.assertEquals(len(results['results']), 1)
        self.assertEquals(results['size'], 1)

        record = results['results'][0]
        self.assertEquals(record['dn'], 'cn=jens,dc=localhost')
        self.assertEquals(record['cn'], ['jens'])
        self.assertEquals(record['multivaluestring'], ['val1','val2','val3'])
        self.assertEquals(record['multivaluelist'], ['val1','val2'])

    def test_insert_readonly(self):
        conn = self._makeOne('host', 636, 'ldap', self._factory, read_only=True)
        self.assertRaises(RuntimeError, conn.insert, 'dc=localhost', 'cn=jens')

    def test_insert_referral(self):
        import ldap
        exc_arg = {'info':'please go to ldap://otherhost:1389'}
        conn, ldap_connection = self._makeRaising( 'add_s'
                                                 , ldap.REFERRAL
                                                 , exc_arg
                                                 )
        conn.insert('dc=localhost', 'cn=jens', attrs={'cn':['jens']})
        self.assertEqual(ldap_connection.conn_string, 'ldap://otherhost:1389')
        self.assertEquals( ldap_connection.args
                         , ('cn=jens,dc=localhost', [('cn', ['jens'])])
                         )

    def test_insert_binary(self):
        conn = self._makeSimple()
        conn.insert('dc=localhost', 'cn=jens', {'objectguid;binary' : u'a'})

        results = conn.search('dc=localhost', fltr='(cn=jens)')
        self.assertEquals(len(results['results']), 1)
        self.assertEquals(results['size'], 1)

        record = results['results'][0]
        self.assertEquals(record['objectguid'], u'a')


def test_suite():
    import sys
    return unittest.findTestCases(sys.modules[__name__])

