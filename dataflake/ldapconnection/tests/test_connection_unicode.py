# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008-2012 Jens Vagelpohl and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" test_connection_unicode: Tests for the LDAPConnection Unicode support

$Id$
"""

import unittest

from dataflake.ldapconnection.tests.base import LDAPConnectionTests


class UnicodeSupportTests(LDAPConnectionTests):

    def test_search_unicode_results(self):
        conn = self._makeSimple()
        conn.api_encoding = None

        attrs = {'displayName': 'Bjørn'}
        conn.insert('dc=localhost', 'cn=føø', attrs=attrs)

        response = conn.search('dc=localhost', fltr='(cn=føø)')
        self.assertEqual(response['size'], 1)

        results = response['results']
        self.assertEqual( results[0]
                        , { 'dn': u'cn=føø,dc=localhost'
                          , 'cn': [u'føø']
                          , 'displayName': [u'Bjørn']
                          }
                        )

    def test_search_raw_results(self):
        conn = self._makeSimple()
        conn.api_encoding = None

        attrs = {'displayName': 'Bjørn'}
        conn.insert('dc=localhost', 'cn=føø', attrs=attrs)

        response = conn.search('dc=localhost', fltr='(cn=føø)', raw=True)
        self.assertEqual(response['size'], 1)

        results = response['results']
        self.assertEqual( results[0]
                        , { 'dn': 'cn=føø,dc=localhost'
                          , 'cn': ['føø']
                          , 'displayName': ['Bjørn']
                          }
                        )

    def test_insert_unicode_data(self):
        conn = self._makeSimple()
        conn.api_encoding = None

        attrs = {'displayName': u'Bjørn'}
        conn.insert(u'dc=localhost', u'cn=føø', attrs=attrs)

        response = conn.search(u'dc=localhost', fltr=u'(cn=føø)')
        self.assertEqual(response['size'], 1)

        results = response['results']
        self.assertEqual( results[0]
                        , { 'dn': u'cn=føø,dc=localhost'
                          , 'cn': [u'føø']
                          , 'displayName': [u'Bjørn']
                          }
                        )

    def test_modify_unicode_data(self):
        conn = self._makeSimple()
        conn.api_encoding = None

        attrs = {'displayName': u'Bjørn'}
        conn.insert(u'dc=localhost', u'cn=føø', attrs=attrs)
        attrs = {'displayName': u'Bjørn Åge'}
        conn.modify(u'cn=føø,dc=localhost', attrs=attrs)

        response = conn.search(u'dc=localhost', fltr=u'(cn=føø)')
        self.assertEqual(response['size'], 1)

        results = response['results']
        self.assertEqual( results[0]
                        , { 'dn': u'cn=føø,dc=localhost'
                          , 'cn': [u'føø']
                          , 'displayName': [u'Bjørn Åge']
                          }
                        )

    def test_modify_multivalued_unicode_data(self):
        conn = self._makeSimple()
        conn.api_encoding = None

        attrs = {'cn': [u'føø', u'Bjørn Åge']}
        conn.insert(u'dc=localhost', u'cn=føø', attrs=attrs)
        attrs = {'cn': [u'føø', u'Bjørn', u'Bjørn Åge']}
        conn.modify(u'cn=føø,dc=localhost', attrs=attrs)
        attrs = {'cn': [u'føø', u'Bjørn']}
        conn.modify(u'cn=føø,dc=localhost', attrs=attrs)

        response = conn.search(u'dc=localhost', fltr=u'(cn=føø)')
        self.assertEqual(response['size'], 1)

        results = response['results']
        self.assertEqual( results[0]
                        , { 'dn': u'cn=føø,dc=localhost'
                          , 'cn': [u'føø', u'Bjørn']
                          }
                        )

        response = conn.search(u'dc=localhost', fltr=u'(cn=Bjørn)')
        self.assertEqual(response['size'], 1)

        results = response['results']
        self.assertEqual( results[0]
                        , { 'dn': u'cn=føø,dc=localhost'
                          , 'cn': [u'føø', u'Bjørn']
                          }
                        )

        response = conn.search(u'dc=localhost', fltr=u'(cn=Bjørn Åge)')
        self.assertEqual(response['size'], 0)

    def test_modify_unicode_rdn(self):
        conn = self._makeSimple()
        conn.api_encoding = None

        attrs = {'displayName': u'Bjørn', 'cn': u'føø'}
        conn.insert(u'dc=localhost', u'cn=føø', attrs=attrs)
        attrs = {'cn': u'bår'}
        conn.modify(u'cn=føø,dc=localhost', attrs=attrs)

        response = conn.search(u'dc=localhost', fltr=u'(cn=bår)')
        self.assertEqual(response['size'], 1)

        results = response['results']
        self.assertEqual( results[0]
                        , { 'dn': u'cn=bår,dc=localhost'
                          , 'cn': [u'bår']
                          , 'displayName': [u'Bjørn']
                          }
                        )

    def test_modify_multivalued_unicode_rdn(self):
        conn = self._makeSimple()
        conn.api_encoding = None

        attrs = {'displayName': u'Bjørn', 'cn': [u'føø', u'Bjørn'],}
        conn.insert(u'dc=localhost', u'cn=føø', attrs=attrs)
        attrs = {'cn': [u'bår', u'Bjørn']}
        conn.modify(u'cn=føø,dc=localhost', attrs=attrs)

        response = conn.search(u'dc=localhost', fltr=u'(cn=bår)')
        self.assertEqual(response['size'], 1)

        results = response['results']
        self.assertEqual( results[0]
                        , { 'dn': u'cn=bår,dc=localhost'
                          , 'cn': [u'bår', u'Bjørn']
                          , 'displayName': [u'Bjørn']
                          }
                        )

    def test_delete_by_unicode_dn(self):
        conn = self._makeSimple()
        conn.api_encoding = None

        attrs = {'displayName': u'Bjørn'}
        conn.insert(u'dc=localhost', u'cn=føø', attrs=attrs)
        conn.delete(u'cn=føø,dc=localhost')

        response = conn.search(u'dc=localhost', fltr=u'(cn=føø)')
        self.assertEqual(response['size'], 0)

    def test_bind_with_valid_unicode_credentials(self):
        from dataflake.ldapconnection.tests import fakeldap
        conn = self._makeSimple()
        conn.api_encoding = None

        attrs = {'userPassword': fakeldap.hash_pwd('secret')}
        conn.insert(u'dc=localhost', u'cn=føø', attrs=attrs)

        response = conn.search( u'dc=localhost'
                              , fltr=u'(cn=føø)'
                              , bind_dn=u'cn=føø,dc=localhost'
                              , bind_pwd=u'secret'
                              )
        self.assertEqual(response['size'], 1)

    def test_bind_with_invalid_unicode_credentials(self):
        import ldap
        from dataflake.ldapconnection.tests import fakeldap
        conn = self._makeSimple()
        conn.api_encoding = None

        attrs = {'userPassword': fakeldap.hash_pwd('secret')}
        conn.insert(u'dc=localhost', u'cn=føø', attrs=attrs)

        self.assertRaises( ldap.INVALID_CREDENTIALS
                         , conn.search
                         , u'dc=localhost'
                         , fltr=u'(cn=føø)'
                         , bind_dn=u'cn=føø,dc=localhost'
                         , bind_pwd=u'geheim'
                         )

    def test_bind_with_valid_unicode_credentials_from_connection(self):
        from dataflake.ldapconnection.tests import fakeldap
        conn = self._makeSimple()
        conn.api_encoding = None

        attrs = {'userPassword': fakeldap.hash_pwd('secret')}
        conn.insert(u'dc=localhost', u'cn=føø', attrs=attrs)

        conn.bind_dn = u'cn=føø,dc=localhost'
        conn.bind_pwd = u'secret'
        response = conn.search( u'dc=localhost'
                              , fltr=u'(cn=føø)'
                              )
        self.assertEqual(response['size'], 1)

    def test_bind_with_invalid_unicode_credentials_from_connection(self):
        import ldap
        from dataflake.ldapconnection.tests import fakeldap
        conn = self._makeSimple()
        conn.api_encoding = None

        attrs = {'userPassword': fakeldap.hash_pwd('secret')}
        conn.insert(u'dc=localhost', u'cn=føø', attrs=attrs)

        conn.bind_dn = u'cn=føø,dc=localhost'
        conn.bind_pwd = u'geheim'
        self.assertRaises( ldap.INVALID_CREDENTIALS
                         , conn.search
                         , u'dc=localhost'
                         , fltr=u'(cn=føø)'
                         )


def test_suite():
    import sys
    return unittest.findTestCases(sys.modules[__name__])

