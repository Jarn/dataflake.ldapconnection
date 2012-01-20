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
""" test_connection_modify: Tests for the LDAPConnection modify method

$Id: test_connection_modify.py 1916 2010-04-12 11:50:39Z jens $
"""

import unittest

from dataflake.ldapconnection.tests.base import LDAPConnectionTests
from dataflake.ldapconnection.tests.dummy import ISO_8859_1_ENCODED
from dataflake.ldapconnection.tests.dummy import ISO_8859_1_UTF8


class ConnectionModifyTests(LDAPConnectionTests):

    def test_modify_noauthentication(self):
        conn = self._makeSimple()
        conn.insert('dc=localhost', 'cn=foo')
        import ldap
        conn.modify( 'cn=foo,dc=localhost'
                   , mod_type=ldap.MOD_ADD
                   , attrs={'b':'b'}
                   )
        connection = conn._getConnection()
        binduid, bindpwd = connection._last_bind[1]
        self.assertEqual(binduid, u'')
        self.assertEqual(bindpwd, '')

    def test_modify_authentication(self):
        conn = self._makeSimple()
        conn.insert('dc=localhost', 'cn=foo')
        bind_dn_apiencoded = 'cn=%s,dc=localhost' % ISO_8859_1_ENCODED
        bind_dn_serverencoded = 'cn=%s,dc=localhost' % ISO_8859_1_UTF8
        self._addRecord(bind_dn_serverencoded, userPassword='foo', cn='foo')
        import ldap
        conn.modify( 'cn=foo,dc=localhost'
                   , mod_type=ldap.MOD_ADD
                   , attrs={'b':'b'}
                   , bind_dn=bind_dn_apiencoded
                   , bind_pwd='foo'
                   )
        connection = conn._getConnection()
        binduid, bindpwd = connection._last_bind[1]
        self.assertEqual(binduid, bind_dn_serverencoded)
        self.assertEqual(bindpwd, 'foo')

    def test_modify_explicit_add(self):
        conn = self._makeSimple()
        conn.insert('dc=localhost', 'cn=foo')
        import ldap
        conn.modify( 'cn=foo,dc=localhost'
                   , mod_type=ldap.MOD_ADD
                   , attrs={'b':'b'}
                   )
        rec = conn.search('dc=localhost', fltr='(cn=foo)')['results'][0]
        self.assertEquals(rec['b'], ['b'])

        # Trying to add an empty new value should not cause more operations
        conn.modify( 'cn=foo,dc=localhost'
                   , mod_type=ldap.MOD_ADD
                   , attrs={'c':''}
                   )
        rec = conn.search('dc=localhost', fltr='(cn=foo)')['results'][0]
        self.failIf(rec.get('c'))

    def test_modify_explicit_modify(self):
        attrs = {'a':'a', 'b': ['x','y','z']}
        conn = self._makeSimple()
        conn.insert('dc=localhost', 'cn=foo', attrs=attrs)
        import ldap
        conn.modify( 'cn=foo,dc=localhost'
                   , mod_type=ldap.MOD_REPLACE
                   , attrs={'a':'y', 'b': ['f','g','h']}
                   )
        rec = conn.search('dc=localhost', fltr='(cn=foo)')['results'][0]
        self.assertEquals(rec['a'], ['y'])
        self.assertEquals(rec['b'], ['f','g','h'])

    def test_modify_explicit_delete(self):
        conn = self._makeSimple()
        conn.insert('dc=localhost', 'cn=foo', attrs={'a': 'a', 'b':'b'})
        import ldap
        conn.modify( 'cn=foo,dc=localhost'
                   , mod_type=ldap.MOD_DELETE
                   , attrs={'a':'a'}
                   )
        rec = conn.search('dc=localhost', fltr='(cn=foo)')['results'][0]
        self.failIf(rec.get('a'))

        # Trying to modify the record by providing an empty or non-matching
        # value should not result in any changes.
        conn.modify( 'cn=foo,dc=localhost'
                   , mod_type=ldap.MOD_DELETE
                   , attrs={'b':''}
                   )
        rec = conn.search('dc=localhost', fltr='(cn=foo)')['results'][0]
        self.assertEquals(rec['b'], ['b'])

        # Trying a deletion with non-matching key and value must fail
        conn.modify( 'cn=foo,dc=localhost'
                   , mod_type=ldap.MOD_DELETE
                   , attrs={'b':'UNKNOWN'}
                   )
        rec = conn.search('dc=localhost', fltr='(cn=foo)')['results'][0]
        self.assertEquals(rec['b'], ['b'])

        # Trying a deletion with partial intersecting values fails as well
        conn.modify( 'cn=foo,dc=localhost'
                   , mod_type=ldap.MOD_DELETE
                   , attrs={'b':['a','b']}
                   )
        rec = conn.search('dc=localhost', fltr='(cn=foo)')['results'][0]
        self.assertEquals(rec['b'], ['b'])

    def test_modify_implicit_add(self):
        conn = self._makeSimple()
        conn.insert('dc=localhost', 'cn=foo', attrs={'a':'a'})
        conn.modify('cn=foo,dc=localhost', attrs={'b':'b'})
        rec = conn.search('dc=localhost', fltr='(cn=foo)')['results'][0]
        self.assertEquals(rec['b'], ['b'])

        # Trying to add an empty new value should not cause more operations
        conn.modify('cn=foo,dc=localhost', attrs={'c':''})
        rec = conn.search('dc=localhost', fltr='(cn=foo)')['results'][0]
        self.failIf(rec.get('c'))

    def test_modify_implicit_modify(self):
        conn = self._makeSimple()
        conn.insert('dc=localhost', 'cn=foo', attrs={'a':'a'})
        conn.modify('cn=foo,dc=localhost', attrs={'a':'y'})
        rec = conn.search('dc=localhost', fltr='(cn=foo)')['results'][0]
        self.assertEquals(rec['a'], ['y'])

    def test_modify_implicit_delete(self):
        conn = self._makeSimple()
        conn.insert('dc=localhost', 'cn=foo', attrs={'a':'a'})
        conn.modify('cn=foo,dc=localhost', attrs={'a':''})
        rec = conn.search('dc=localhost', fltr='(cn=foo)')['results'][0]
        self.failIf(rec.get('a'))

        # Trying to modify the record by providing an empty non-existing key
        # should not result in more operations.
        conn.modify('cn=foo,dc=localhost', attrs={'b':''})
        rec = conn.search('dc=localhost', fltr='(cn=foo)')['results'][0]
        self.failIf(rec.get('b'))

    def test_modify_readonly(self):
        conn = self._makeOne('host', 636, 'ldap', self._factory, read_only=True)
        self.assertRaises(RuntimeError, conn.modify, 'cn=foo', {})

    def test_modify_binary(self):
        conn = self._makeSimple()
        conn.insert('dc=localhost', 'cn=foo', attrs={'objectguid':'a'})
        conn.modify('cn=foo,dc=localhost', attrs={'objectguid;binary': u'y'})
        rec = conn.search('dc=localhost', fltr='(cn=foo)')['results'][0]
        self.assertEquals(rec['objectguid'], u'y')

    def test_modify_modrdn(self):
        conn = self._makeSimple()
        conn.insert('dc=localhost', 'cn=foo')
        conn.modify('cn=foo,dc=localhost', attrs={'cn':'bar'})
        rec = conn.search('dc=localhost', fltr='(cn=bar)')['results'][0]
        self.assertEquals(rec['cn'], ['bar'])

    def test_modify_referral(self):
        import ldap
        exc_arg = {'info':'please go to ldap://otherhost:1389'}
        conn, ldap_connection = self._makeRaising( 'modify_s'
                                                 , ldap.REFERRAL
                                                 , exc_arg
                                                 )
        conn.insert('dc=localhost', 'cn=foo')

        conn.modify('cn=foo,dc=localhost', attrs={'a':'y'})
        self.assertEqual(ldap_connection.conn_string, 'ldap://otherhost:1389')
        dn, modlist = ldap_connection.args
        self.assertEquals(dn, 'cn=foo,dc=localhost')
        self.assertEquals(modlist, [(0, 'a', ['y'])])

    def test_modify_nonexisting_raises(self):
        import ldap
        conn = self._makeSimple()
        self.assertRaises( ldap.NO_SUCH_OBJECT
                         , conn.modify
                         , 'cn=UNKNOWN'
                         , attrs={'a':'y'}
                         )


def test_suite():
    import sys
    return unittest.findTestCases(sys.modules[__name__])

