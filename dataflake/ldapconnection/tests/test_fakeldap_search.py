# -*- coding: utf-8 -*-
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
""" test_fakeldap_search: Tests for the FakeLDAP search_s method

$Id$
"""

import doctest
import unittest

from dataflake.ldapconnection.tests.base import FakeLDAPTests

class FakeLDAPSearchTests(FakeLDAPTests):

    def test_search_specific(self):
        conn = self._makeOne()
        self._addUser('foo')
        self._addUser('footwo')
        self._addUser('thirdfoo')

        res = conn.search_s('ou=users,dc=localhost', query='(cn=foo)')
        dn_values = [dn for (dn, attr_dict) in res]
        self.assertEquals(len(dn_values), 1)
        self.assertEquals(dn_values, ['cn=foo,ou=users,dc=localhost'])

    def test_search_nonspecific(self):
        conn = self._makeOne()
        self._addUser('foo')
        self._addUser('bar')
        self._addUser('baz')

        res = conn.search_s('ou=users,dc=localhost', query='(objectClass=*)')
        dn_values = [dn for (dn, attr_dict) in res]
        self.assertEquals(len(dn_values), 3)
        # Note: searches for all results and not scope BASE will return
        # RDNs instead of full DNs
        self.assertEquals( set(dn_values)
                         , set(['cn=foo', 'cn=bar', 'cn=baz'])
                         )

    def test_search_nonspecific_scope_base(self):
        import ldap
        conn = self._makeOne()
        user_dn, password = self._addUser('foo')

        res = conn.search_s( user_dn
                           , scope=ldap.SCOPE_BASE
                           , query='(objectClass=*)'
                           )
        dn_values = [dn for (dn, attr_dict) in res]
        self.assertEquals(len(dn_values), 1)
        self.assertEquals(dn_values, ['cn=foo,ou=users,dc=localhost'])

    def test_search_full_wildcard(self):
        conn = self._makeOne()
        self._addUser('foo')
        self._addUser('footwo')
        self._addUser('threefoo')

        res = conn.search_s('ou=users,dc=localhost', query='(cn=*)')
        dn_values = [dn for (dn, attr_dict) in res]
        self.assertEquals(len(dn_values), 3)
        self.assertEquals( set(dn_values)
                         , set( [ 'cn=foo,ou=users,dc=localhost'
                                , 'cn=footwo,ou=users,dc=localhost'
                                , 'cn=threefoo,ou=users,dc=localhost'
                                ] )
                         )

    def test_search_startswithendswith_wildcard(self):
        conn = self._makeOne()
        self._addUser('foo')
        self._addUser('onefootwo')
        self._addUser('threefoo')
        self._addUser('bar')

        res = conn.search_s('ou=users,dc=localhost', query='(cn=*foo*)')
        dn_values = [dn for (dn, attr_dict) in res]
        self.assertEquals(len(dn_values), 3)
        self.assertEquals( set(dn_values)
                         , set( [ 'cn=foo,ou=users,dc=localhost'
                                , 'cn=onefootwo,ou=users,dc=localhost'
                                , 'cn=threefoo,ou=users,dc=localhost'
                                ] )
                         )

    def test_search_endswith_wildcard(self):
        conn = self._makeOne()
        self._addUser('foo')
        self._addUser('footwo')
        self._addUser('threefoo')

        res = conn.search_s('ou=users,dc=localhost', query='(cn=*foo)')
        dn_values = [dn for (dn, attr_dict) in res]
        self.assertEquals(len(dn_values), 2)
        self.assertEquals( set(dn_values)
                         , set( [ 'cn=foo,ou=users,dc=localhost'
                                , 'cn=threefoo,ou=users,dc=localhost'
                                ] )
                         )

    def test_search_startswith_wildcard(self):
        conn = self._makeOne()
        self._addUser('foo')
        self._addUser('footwo')
        self._addUser('threefoo')

        res = conn.search_s('ou=users,dc=localhost', query='(cn=foo*)')
        dn_values = [dn for (dn, attr_dict) in res]
        self.assertEquals(len(dn_values), 2)
        self.assertEquals( set(dn_values)
                         , set( [ 'cn=foo,ou=users,dc=localhost'
                                , 'cn=footwo,ou=users,dc=localhost'
                                ] )
                         )

    def test_search_anded_filter(self):
        conn = self._makeOne()
        self._addUser('foo')
        self._addUser('bar')
        self._addUser('baz')

        query_success = '(&(cn=foo)(objectClass=person))'
        res = conn.search_s('ou=users,dc=localhost', query=query_success)
        dn_values = [dn for (dn, attr_dict) in res]
        self.assertEquals(len(dn_values), 1)
        self.assertEquals(dn_values, ['cn=foo,ou=users,dc=localhost'])

        query_failure = '(&(cn=foo)(objectClass=inetOrgPerson))'
        self.failIf(conn.search_s('ou=users,dc=localhost', query=query_failure))

    def test_search_ored_filter(self):
        conn = self._makeOne()
        self._addUser('foo')
        self._addUser('bar')
        self._addUser('baz')

        res = conn.search_s( 'ou=users,dc=localhost'
                           , query='(|(cn=foo)(cn=bar))'
                           )
        dn_values = [dn for (dn, attr_dict) in res]
        self.assertEquals(len(dn_values), 2)
        self.assertEquals( set(dn_values)
                         , set( [ 'cn=foo,ou=users,dc=localhost'
                                , 'cn=bar,ou=users,dc=localhost'
                                ] )
                         )
    
    def test_search_invalid_base(self):
        import ldap
        conn = self._makeOne()
        self._addUser('foo')
        self.assertRaises( ldap.NO_SUCH_OBJECT
                         , conn.search_s
                         , 'o=base'
                         , query='(objectClass=*)'
                         )

    def test_search_by_mail(self):
        conn = self._makeOne()
        self._addUser('foo', mail='foo@foo.com')
        self._addUser('bar', mail='bar@bar.com')
        self._addUser('baz', mail='baz@baz.com')

        res = conn.search_s( 'ou=users,dc=localhost'
                           , query='(|(mail=foo@foo.com)(mail=bar@bar.com))'
                           )
        dn_values = [dn for (dn, attr_dict) in res]
        self.assertEquals(len(dn_values), 2)
        self.assertEquals( set(dn_values)
                         , set( [ 'cn=foo,ou=users,dc=localhost'
                                , 'cn=bar,ou=users,dc=localhost'
                                ] )
                         )

    def test_search_by_utf8(self):
        conn = self._makeOne()
        self._addUser('føø')
        self._addUser('bår')
        self._addUser('baz')

        res = conn.search_s( 'ou=users,dc=localhost'
                           , query='(|(cn=føø)(cn=bår))'
                           )
        dn_values = [dn for (dn, attr_dict) in res]
        self.assertEquals(len(dn_values), 2)
        self.assertEquals( set(dn_values)
                         , set( [ 'cn=føø,ou=users,dc=localhost'
                                , 'cn=bår,ou=users,dc=localhost'
                                ] )
                         )

    def test_return_all_attributes(self):
        conn = self._makeOne()
        self._addUser('foo', mail='foo@foo.com')

        res = conn.search_s( 'ou=users,dc=localhost'
                           , query='(cn=foo)'
                           , attrs=None
                           )
        self.assertEquals(len(res), 1)
        dn, attr_dict = res[0]
        self.assertEquals(dn, 'cn=foo,ou=users,dc=localhost')
        self.assertTrue('cn' in attr_dict)
        self.assertTrue('mail' in attr_dict)
        self.assertTrue('userPassword' in attr_dict)
        self.assertTrue('objectClass' in attr_dict)

    def test_return_filtered_attributes(self):
        conn = self._makeOne()
        self._addUser('foo', mail='foo@foo.com')

        res = conn.search_s( 'ou=users,dc=localhost'
                           , query='(cn=foo)'
                           , attrs=['cn', 'mail']
                           )
        self.assertEquals(len(res), 1)
        dn, attr_dict = res[0]
        self.assertEquals(dn, 'cn=foo,ou=users,dc=localhost')
        self.assertTrue('cn' in attr_dict)
        self.assertTrue('mail' in attr_dict)
        self.assertFalse('userPassword' in attr_dict)
        self.assertFalse('objectClass' in attr_dict)


def test_suite():
    import sys
    return unittest.findTestCases(sys.modules[__name__])
