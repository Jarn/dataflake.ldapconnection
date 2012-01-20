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
""" test_connection_basic: Basic tests for the LDAPConnection class

$Id: test_connection_basic.py 1895 2010-02-04 21:09:28Z jens $
"""

import unittest

from dataflake.ldapconnection.tests.base import LDAPConnectionTests
from dataflake.ldapconnection.tests.dummy import ISO_8859_1_ENCODED
from dataflake.ldapconnection.tests.dummy import ISO_8859_1_UNICODE
from dataflake.ldapconnection.tests.dummy import ISO_8859_1_UTF8
from dataflake.ldapconnection.tests.dummy import ISO_8859_7_ENCODED
from dataflake.ldapconnection.tests.dummy import ISO_8859_7_UNICODE
from dataflake.ldapconnection.tests.dummy import ISO_8859_7_UTF8
from dataflake.ldapconnection.tests.fakeldap import FakeLDAPConnection

class ConnectionBasicTests(LDAPConnectionTests):

    def test_conformance(self):
        # Test to see if the given class implements the ILDAPConnection
        # interface completely.
        from zope.interface.verify import verifyClass
        from dataflake.ldapconnection.interfaces import ILDAPConnection
        verifyClass(ILDAPConnection, self._getTargetClass())

    def test_constructor_defaults(self):
        conn = self._makeSimple()
        self.assertEqual(conn.bind_dn, u'')
        self.assertEqual(conn.bind_pwd, '')
        self.failIf(conn.read_only)
        self.assertEqual(conn._getConnection(), None)
        self.assertEqual(conn.c_factory, FakeLDAPConnection)

    def test_constructor(self):
        bind_dn_encoded = 'cn=%s,dc=localhost' % ISO_8859_1_ENCODED
        bind_dn_unicode = u'cn=%s,dc=localhost' % ISO_8859_1_UNICODE
        conn = self._makeOne( 'localhost'
                            , 389
                            , 'ldap'
                            , 'factory'
                            , bind_dn=bind_dn_encoded
                            , bind_pwd='foo'
                            , read_only=True
                            , conn_timeout=5
                            , op_timeout=10
                            , logger='logger'
                            )
        self.assertEqual(conn.bind_dn, bind_dn_unicode)
        self.assertEqual(conn.bind_pwd, 'foo')
        self.failUnless(conn.read_only)
        self.assertEqual(conn._getConnection(), None)
        self.assertEqual(conn.c_factory, 'factory')
        self.assertEqual(conn.logger(), 'logger')

    def test_constructor_unicode_bind_dn(self):
        bind_dn_unicode = u'cn=%s,dc=localhost' % ISO_8859_1_UNICODE
        conn = self._makeOne( 'localhost'
                            , 389
                            , 'ldap'
                            , 'factory'
                            , bind_dn=bind_dn_unicode
                            , bind_pwd='foo'
                            )
        self.assertEqual(conn.bind_dn, bind_dn_unicode)

    def test_encode_incoming(self):
        conn = self._makeSimple()

        self.assertEquals(conn._encode_incoming(None), None)

        conn.api_encoding = None
        conn.ldap_encoding = None
        self.assertEquals( conn._encode_incoming(ISO_8859_7_UNICODE)
                         , ISO_8859_7_UNICODE
                         )

        conn.api_encoding = 'iso-8859-7'
        conn.ldap_encoding = None
        self.assertEquals( conn._encode_incoming(ISO_8859_7_ENCODED)
                         , ISO_8859_7_UNICODE
                         )

        conn.api_encoding = None
        conn.ldap_encoding = 'iso-8859-7'
        self.assertEquals( conn._encode_incoming(ISO_8859_7_UNICODE)
                         , ISO_8859_7_ENCODED
                         )

        conn.api_encoding = 'iso-8859-7'
        conn.ldap_encoding = 'UTF-8'
        self.assertEquals( conn._encode_incoming(ISO_8859_7_ENCODED)
                         , ISO_8859_7_UTF8
                         )

    def test_encode_outgoing(self):
        conn = self._makeSimple()

        self.assertEquals(conn._encode_outgoing(None), None)

        conn.api_encoding = None
        conn.ldap_encoding = None
        self.assertEquals( conn._encode_outgoing(ISO_8859_7_UNICODE)
                         , ISO_8859_7_UNICODE
                         )

        conn.api_encoding = 'iso-8859-7'
        conn.ldap_encoding = None
        self.assertEquals( conn._encode_outgoing(ISO_8859_7_UNICODE)
                         , ISO_8859_7_ENCODED
                         )

        conn.api_encoding = None
        conn.ldap_encoding = 'iso-8859-7'
        self.assertEquals( conn._encode_outgoing(ISO_8859_7_ENCODED)
                         , ISO_8859_7_UNICODE
                         )

        conn.api_encoding = 'iso-8859-7'
        conn.ldap_encoding = 'UTF-8'
        self.assertEquals( conn._encode_outgoing(ISO_8859_7_UTF8)
                         , ISO_8859_7_ENCODED
                         )

def test_suite():
    import sys
    return unittest.findTestCases(sys.modules[__name__])

