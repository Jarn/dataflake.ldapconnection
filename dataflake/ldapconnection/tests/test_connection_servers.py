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
""" test_connection: Tests for the LDAPConnection class

$Id: test_connection_servers.py 1895 2010-02-04 21:09:28Z jens $
"""

import ldapurl
import unittest

from dataflake.ldapconnection.tests.base import LDAPConnectionTests


class ConnectionServerTests(LDAPConnectionTests):

    def test_add_via_constructor(self):
        conn = self._makeSimple()
        self.assertEquals(len(conn.servers.values()), 1)
        server = conn.servers.values()[0]
        self.assertEquals(server['url'], 'ldap://host:636')
        self.assertEqual(server['conn_timeout'], -1)
        self.assertEqual(server['op_timeout'], -1)

    def test_add_server(self):
        conn = self._makeSimple()
        conn.addServer('localhost', 636, 'ldaps', conn_timeout=5, op_timeout=10)
        servers = conn.servers.values()

        self.assertEquals(len(servers), 2)
        self.assertEquals( servers
                         , [ { 'url': 'ldap://host:636'
                               , 'op_timeout': -1
                               , 'conn_timeout': -1
                               , 'start_tls': False
                               }
                             , { 'url': 'ldaps://localhost:636'
                               , 'op_timeout': 10
                               , 'conn_timeout': 5
                               , 'start_tls': False
                               }
                             ]
                         )

    def test_add_server_ldaptls(self):
        conn = self._makeSimple()
        conn.addServer('localhost',389,'ldaptls',conn_timeout=5,op_timeout=10)
        servers = conn.servers.values()

        self.assertEquals(len(servers), 2)
        self.assertEquals( servers
                         , [ { 'url': 'ldap://localhost:389'
                             , 'op_timeout': 10
                             , 'conn_timeout': 5
                             , 'start_tls': True
                             }
                           , { 'url': 'ldap://host:636'
                             , 'op_timeout': -1
                             , 'conn_timeout': -1
                             , 'start_tls': False
                             }
                           ]
                         )

    def test_add_server_existing(self):
        # If a LDAP server definition with the same LDAP URL exists, it
        # will be replaced with the new values.
        conn = self._makeSimple()
        existing = conn.servers.values()[0]
        ldap_url = ldapurl.LDAPUrl(existing['url'])
        host, port = ldap_url.hostport.split(':')
        protocol = ldap_url.urlscheme

        conn.addServer(host, port, protocol, conn_timeout=10, op_timeout=15)

        self.assertEquals(len(conn.servers.values()), 1)
        server = conn.servers.values()[0]
        self.assertEquals(server['url'], 'ldap://host:636')
        self.assertEqual(server['conn_timeout'], 10)
        self.assertEqual(server['op_timeout'], 15)

    def test_remove_server(self):
        conn = self._makeSimple()
        existing = conn.servers.values()[0]
        ldap_url = ldapurl.LDAPUrl(existing['url'])
        host, port = ldap_url.hostport.split(':')
        protocol = ldap_url.urlscheme

        conn.removeServer(host, port, protocol)

        self.assertEquals(len(conn.servers.values()), 0)

    def test_remove_server_nonexisting(self):
        conn = self._makeSimple()

        conn.removeServer('nonexisting', 389, 'ldap')

        self.assertEquals(len(conn.servers.values()), 1)
        server = conn.servers.values()[0]
        self.assertEquals(server['url'], 'ldap://host:636')
        self.assertEqual(server['conn_timeout'], -1)
        self.assertEqual(server['op_timeout'], -1)


def test_suite():
    import sys
    return unittest.findTestCases(sys.modules[__name__])

