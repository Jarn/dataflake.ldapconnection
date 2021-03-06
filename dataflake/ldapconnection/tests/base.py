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
""" unit tests base classes

$Id$
"""

import unittest

from dataflake.ldapconnection.connection import connection_cache
from dataflake.ldapconnection.tests import fakeldap

class LDAPConnectionTests(unittest.TestCase):

    def setUp(self):
        super(LDAPConnectionTests, self).setUp()
        # Put a record into the tree
        fakeldap.addTreeItems('dc=localhost')

    def tearDown(self):
        super(LDAPConnectionTests, self).tearDown()
        fakeldap.clearTree()
        connection_cache.invalidate()

    def _getTargetClass(self):
        from dataflake.ldapconnection.connection import LDAPConnection
        return LDAPConnection

    def _makeOne(self, *args, **kw):
        conn = self._getTargetClass()(*args, **kw)
        conn.api_encoding = 'iso-8859-1'
        conn.ldap_encoding = 'UTF-8'
        return conn

    def _makeSimple(self):
        conn = self._makeOne('host', 636, 'ldap', fakeldap.FakeLDAPConnection)
        conn.api_encoding = 'iso-8859-1'
        conn.ldap_encoding = 'UTF-8'
        return conn

    def _makeRaising(self, raise_on, exc_class, exc_arg=None):
        ldap_connection = fakeldap.RaisingFakeLDAPConnection('conn_string')
        ldap_connection.setExceptionAndMethod(raise_on, exc_class, exc_arg)
        def factory(conn_string):
            ldap_connection.conn_string = conn_string
            return ldap_connection
        conn = self._makeOne('host', 389, 'ldaptls', factory)

        return conn, ldap_connection

    def _makeFixedResultConnection(self, results):
        ldap_connection = fakeldap.FixedResultFakeLDAPConnection()
        ldap_connection.search_results = results
        def factory(conn_string):
            ldap_connection.conn_string = conn_string
            return ldap_connection
        conn = self._makeOne('host', 389, 'ldaptls', factory)

        return conn

    def _factory(self, connection_string):
        of = fakeldap.FakeLDAPConnection(connection_string)
        return of

    def _addRecord(self, dn, **kw):
        record = fakeldap.addTreeItems(dn)
        for key, value in kw.items():
            if key.lower() == 'userpassword':
                value = [fakeldap.hash_pwd(value)]
            elif isinstance(value, basestring):
                value = [value]
            record[key] = value


class FakeLDAPTests(unittest.TestCase):

    def setUp(self):
        from dataflake.ldapconnection.tests import fakeldap
        fakeldap.addTreeItems('ou=users,dc=localhost')
        fakeldap.addTreeItems('ou=groups,dc=localhost')

    def tearDown(self):
        from dataflake.ldapconnection.tests import fakeldap
        fakeldap.clearTree()

    def _getTargetClass(self):
        from dataflake.ldapconnection.tests.fakeldap import FakeLDAPConnection
        return FakeLDAPConnection

    def _makeOne(self, *args, **kw):
        conn = self._getTargetClass()(*args, **kw)
        return conn

    def _addUser(self, name, mail=None):
        conn = self._makeOne()
        user_dn = 'cn=%s,ou=users,dc=localhost' % name
        user_pwd = '%s_secret' % name

        if conn.hash_password:
            pwd = fakeldap.hash_pwd(user_pwd)
        else:
            pwd = user_pwd

        user = [ ('cn', [name])
               , ('userPassword', [pwd])
               , ('objectClass', ['top', 'person'])
               ]
        if mail is not None:
            user.append(('mail', [mail]))

        conn.add_s(user_dn, user)
        return (user_dn, user_pwd)

    def _addGroup(self, name, members=None):
        conn = self._makeOne()
        group_dn = 'cn=%s,ou=groups,dc=localhost' % name

        group = [ ('cn', [name])
                , ('objectClass', ['top', 'group'])
                ]
        if members is not None:
            members = ['cn=%s,ou=users,dc=localhost' % x for x in members]
            group.append((conn.member_attr, members))

        conn.add_s(group_dn, group)
        return group_dn

