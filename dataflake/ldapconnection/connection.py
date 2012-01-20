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
""" LDAPConnection: A class modeling a LDAP server connection

Instances of this class offer a simplified API to do searches, insertions, 
deletions or modifications.

$Id$
"""

import codecs
import ldap
from ldap.dn import explode_dn
from ldap.dn import dn2str
from ldap.dn import str2dn
from ldap.filter import filter_format
from ldap.ldapobject import ReconnectLDAPObject
import ldapurl
import logging
from random import random

from zope.interface import implements

from dataflake.cache.simple import LockingSimpleCache
from dataflake.ldapconnection.interfaces import ILDAPConnection
from dataflake.ldapconnection.utils import BINARY_ATTRIBUTES
from dataflake.ldapconnection.utils import escape_dn

default_logger = logging.getLogger('dataflake.ldapconnection')
connection_cache = LockingSimpleCache()
_marker = ()


class LDAPConnection(object):
    """ LDAPConnection object

    See `interfaces.py` for interface documentation.
    """

    implements(ILDAPConnection)

    def __init__( self, host='', port=389, protocol='ldap'
                , c_factory=ReconnectLDAPObject, rdn_attr='', bind_dn=''
                , bind_pwd='', read_only=False
                , conn_timeout=-1, op_timeout=-1, logger=None
                ):
        """ LDAPConnection initialization
        """
        # Empty values here mean "use unicode"
        self.ldap_encoding = 'UTF-8'
        self.api_encoding = 'iso-8859-15'

        if isinstance(bind_dn, unicode):
            bind_dn = bind_dn.encode(self.api_encoding)
        self.bind_dn = escape_dn(bind_dn).decode(self.api_encoding)
        self.bind_pwd = bind_pwd
        self.read_only = read_only
        self.c_factory = c_factory
        self._logger = logger
        self.hash = id(self) + random()

        self.servers = {}
        if host:
            self.addServer(host, port, protocol, conn_timeout, op_timeout)

    def logger(self):
        """ Get the logger
        """
        if self._logger is None:
            return default_logger

        return self._logger

    def addServer(self, host, port, protocol, conn_timeout=-1, op_timeout=-1):
        """ Add a server definition to the list of servers used
        """
        start_tls = False
        if protocol == 'ldaptls':
            protocol = 'ldap'
            start_tls = True
        l = ldapurl.LDAPUrl(urlscheme=protocol, hostport='%s:%s' % (host, port))
        server_url = l.initializeUrl()
        self.servers[server_url] = { 'url' : server_url
                                   , 'conn_timeout' : conn_timeout
                                   , 'op_timeout' : op_timeout
                                   , 'start_tls': start_tls
                                   }

    def removeServer(self, host, port, protocol):
        """ Remove a server definition from the list of servers used
        """
        l = ldapurl.LDAPUrl(urlscheme=protocol, hostport='%s:%s' % (host, port))
        server_url = l.initializeUrl()
        if server_url in self.servers.keys():
            del self.servers[server_url]

    def connect(self, bind_dn=None, bind_pwd=None):
        """ initialize an ldap server connection 

        This method returns an instance of the underlying `python-ldap` 
        connection class. It does not need to be called explicitly, all
        other operations call it implicitly.
        """
        if len(self.servers.keys()) == 0:
            raise RuntimeError('No servers defined')

        if bind_dn is None:
            bind_dn = self._encode_bind_dn()
            bind_pwd = self.bind_pwd
        else:
            bind_dn = escape_dn(self._encode_bind_dn(bind_dn))

        conn = self._getConnection()
        if conn is None:
            for server in self.servers.values():
                try:
                    conn = self._connect( server['url']
                                        , conn_timeout=server['conn_timeout']
                                        , op_timeout=server['op_timeout']
                                        )
                    if server.get('start_tls', None):
                        conn.start_tls_s()
                    break
                except (ldap.SERVER_DOWN, ldap.TIMEOUT, ldap.LOCAL_ERROR), e:
                    conn = None
                    continue

            if conn is None:
                exception_string = str(e or 'no exception')
                msg = 'Failure connecting, last attempt: %s (%s)' % (
                            server['url'], str(e or 'no exception'))
                self.logger().critical(msg, exc_info=1)

                if e:
                    raise e

            connection_cache.set(self.hash, conn)

        last_bind = getattr(conn, '_last_bind', None)
        if ( not last_bind or
             ( last_bind[1][0] != bind_dn and 
               last_bind[1][1] != bind_pwd ) ):
            conn.simple_bind_s(bind_dn, bind_pwd)

        return conn

    def _getConnection(self):
        """ Private helper to get my connection out of the cache
        """
        return connection_cache.get(self.hash)

    def _connect( self
                , connection_string
                , conn_timeout=5
                , op_timeout=-1
                ):
        """ Factored out to allow usage by other pieces 

        user_dn is assumed to have been encoded/escaped correctly
        """
        connection = self.c_factory(connection_string)

        # Deny auto-chasing of referrals to be safe, we handle them instead
        try:
            connection.set_option(ldap.OPT_REFERRALS, ldap.DEREF_NEVER)
        except ldap.LDAPError: # Cannot set referrals, so do nothing
            pass

        # Set the connection timeout
        if conn_timeout > 0:
            connection.set_option(ldap.OPT_NETWORK_TIMEOUT, conn_timeout)

        # Set the operations timeout
        if op_timeout > 0:
            connection.timeout = op_timeout

        return connection

    def search( self
              , base
              , scope=ldap.SCOPE_SUBTREE
              , fltr='(objectClass=*)'
              , attrs=None
              , convert_filter=True
              , bind_dn=None
              , bind_pwd=None
              ):
        """ Search for entries in the database
        """
        result = {'size': 0, 'results': [], 'exception': ''}
        if convert_filter:
            fltr = self._encode_incoming(fltr)
        base = escape_dn(self._encode_incoming(base))
        connection = self.connect(bind_dn=bind_dn, bind_pwd=bind_pwd)

        try:
            res = connection.search_s(base, scope, fltr, attrs)
        except ldap.PARTIAL_RESULTS:
            res_type, res = connection.result(all=0)
        except ldap.REFERRAL, e:
            connection = self._handle_referral(e)

            try:
                res = connection.search_s(base, scope, fltr, attrs)
            except ldap.PARTIAL_RESULTS:
                res_type, res = connection.result(all=0)

        for rec_dn, rec_dict in res:
            # When used against Active Directory, "rec_dict" may not be
            # be a dictionary in some cases (instead, it can be a list)
            # An example of a useless "res" entry that can be ignored
            # from AD is
            # (None, ['ldap://ForestDnsZones.PORTAL.LOCAL/DC=ForestDnsZones,DC=PORTAL,DC=LOCAL'])
            # This appears to be some sort of internal referral, but
            # we can't handle it, so we need to skip over it.
            try:
                items =  rec_dict.items()
            except AttributeError:
                # 'items' not found on rec_dict
                continue

            for key, value in items:
                if key.lower() not in BINARY_ATTRIBUTES:
                    if not isinstance(value, str):
                        for i in range(len(value)):
                            value[i] = self._encode_outgoing(value[i])
                    else:
                        rec_dict[key] = self._encode_outgoing(value)

            rec_dict['dn'] = self._encode_outgoing(rec_dn)

            result['results'].append(rec_dict)
            result['size'] += 1

        return result

    def insert(self, base, rdn, attrs=None, bind_dn=None, bind_pwd=None):
        """ Insert a new record 

        attrs is expected to be a mapping where the value may be a string
        or a sequence of strings. 
        Multiple values may be expressed as a single string if the values 
        are semicolon-delimited.
        Values can be marked as binary values, meaning they are not encoded
        as UTF-8, by appending ';binary' to the key.
        """
        self._complainIfReadOnly()
        base = escape_dn(self._encode_incoming(base))
        rdn = escape_dn(self._encode_incoming(rdn))

        dn = rdn + ',' + base
        attribute_list = []
        attrs = attrs and attrs or {}

        for attr_key, values in attrs.items():
            if attr_key.endswith(';binary'):
                is_binary = True
                attr_key = attr_key[:-7]
            else:
                is_binary = False

            if isinstance(values, basestring) and not is_binary:
                values = [x.strip() for x in values.split(';')]

            if values != ['']:
                if not is_binary:
                    values = [self._encode_incoming(x) for x in values]
                attribute_list.append((attr_key, values))

        try:
            connection = self.connect(bind_dn=bind_dn, bind_pwd=bind_pwd)
            connection.add_s(dn, attribute_list)
        except ldap.REFERRAL, e:
            connection = self._handle_referral(e)
            connection.add_s(dn, attribute_list)

    def delete(self, dn, bind_dn=None, bind_pwd=None):
        """ Delete a record 
        """
        self._complainIfReadOnly()

        dn = escape_dn(self._encode_incoming(dn))

        try:
            connection = self.connect(bind_dn=bind_dn, bind_pwd=bind_pwd)
            connection.delete_s(dn)
        except ldap.REFERRAL, e:
            connection = self._handle_referral(e)
            connection.delete_s(dn)

    def modify(self, dn, mod_type=None, attrs=None, bind_dn=None, bind_pwd=None):
        """ Modify a record 
        """
        self._complainIfReadOnly()

        unescaped_dn = self._encode_incoming(dn)
        dn = escape_dn(unescaped_dn)
        res = self.search( base=unescaped_dn
                         , scope=ldap.SCOPE_BASE
                         , bind_dn=bind_dn
                         , bind_pwd=bind_pwd
                         )
        attrs = attrs and attrs or {}
        cur_rec = res['results'][0]
        mod_list = []

        for key, values in attrs.items():

            if key.endswith(';binary'):
                key = key[:-7]
            elif isinstance(values, basestring):
                values = [self._encode_incoming(x) for x in values.split(';')]
            else:
                values = [self._encode_incoming(x) for x in values]

            if mod_type is None:
                if not cur_rec.has_key(key) and values != ['']:
                    mod_list.append((ldap.MOD_ADD, key, values))
                elif cur_rec.get(key,['']) != values and values not in ([''],[]):
                    mod_list.append((ldap.MOD_REPLACE, key, values))
                elif cur_rec.has_key(key) and values in ([''], []):
                    mod_list.append((ldap.MOD_DELETE, key, None))
            elif values == [''] and mod_type in (ldap.MOD_ADD, ldap.MOD_DELETE):
                continue
            elif ( mod_type == ldap.MOD_DELETE and
                   set(values) != set(cur_rec.get(key, [])) ):
                continue
            else:
                mod_list.append((mod_type, key, values))

        try:
            connection = self.connect(bind_dn=bind_dn, bind_pwd=bind_pwd)

            dn_parts = str2dn(dn)
            rdn = dn_parts[0]
            rdn_attr = rdn[0][0]
            raw_rdn = attrs.get(rdn_attr, '')
            if isinstance(raw_rdn, basestring):
                raw_rdn = [raw_rdn]
            new_rdn = raw_rdn[0]

            if new_rdn and new_rdn != cur_rec.get(rdn_attr)[0]:
                rdn_value = self._encode_incoming(new_rdn)
                dn_parts[0] = [(rdn_attr, rdn_value, 1)]
                raw_utf8_rdn = self._encode_incoming(rdn_attr + '=' + rdn_value)
                new_rdn = escape_dn(raw_utf8_rdn)
                connection.modrdn_s(dn, new_rdn)
                dn = dn2str(dn_parts)

            if mod_list:
                connection.modify_s(dn, mod_list)
            else:
                debug_msg = 'Nothing to modify: %s' % dn
                self.logger().debug(debug_msg)

        except ldap.REFERRAL, e:
            connection = self._handle_referral(e)
            connection.modify_s(dn, mod_list)

    def _handle_referral(self, exception):
        """ Handle a referral specified in the passed-in exception 
        """
        payload = exception.args[0]
        info = payload.get('info')
        ldap_url = info[info.find('ldap'):]

        if ldapurl.isLDAPUrl(ldap_url):
            conn_str = ldapurl.LDAPUrl(ldap_url).initializeUrl()
            conn = self._connect(conn_str)
            conn.simple_bind_s(self._encode_bind_dn(), self.bind_pwd)
            return conn
        else:
            raise ldap.CONNECT_ERROR, 'Bad referral "%s"' % str(exception)

    def _complainIfReadOnly(self):
        """ Raise RuntimeError if the connection is set to `read-only`

        This method should be called before any directory tree modfication
        """
        if self.read_only:
            raise RuntimeError(
                'Running in read-only mode, directory modifications disabled')

    def _encode_incoming(self, value):
        """ Encode a string value to the encoding set for the LDAP server

        - if "value" is unicode, it will be encoded to self.ldap_encoding, but
          only if self.ldap_encoding is set.
        - if "value" is not unicode, it is assumed to be encoded as 
          self.api_encoding. It is decoded and encoded to self.ldap_encoding
          if self.ldap_encoding is set, unless self.api_encoding and 
          self.ldap_encoding are identical. In that case the passed-in value 
          is handed back unchanged.
        """
        if value is None:
            return None

        elif isinstance(value, unicode):
            if self.ldap_encoding:
                value = value.encode(self.ldap_encoding)

        else:
            if self.api_encoding != self.ldap_encoding:
                value = value.decode(self.api_encoding)

                if self.ldap_encoding:
                    value = value.encode(self.ldap_encoding)
        
        return value

    def _encode_outgoing(self, value):
        """ Encode a string value to the API encoding

        - if "value" is unicode, it will be encoded to self.api_encoding, but
          only if self.ldap_encoding is set.
        - if "value" is not unicode, it is assumed to be encoded as 
          self.ldap_encoding. It is decoded and encoded to self.api_encoding
          if self.api_encoding is set, unless self.ldap_encoding and 
          self.api_encoding are identical. In that case the passed-in value 
          is handed back unchanged.
        """
        if value is None:
            return None

        elif isinstance(value, unicode):
            if self.api_encoding:
                value = value.encode(self.api_encoding)

        else:
            if self.api_encoding != self.ldap_encoding:
                value = value.decode(self.ldap_encoding)

                if self.api_encoding:
                    value = value.encode(self.api_encoding)
        
        return value

    def _encode_bind_dn(self, dn=None):
        """ Make sure the stored bind DN is encoded correctly upon access
        """
        bind_dn = dn or getattr(self, 'bind_dn', '')

        if not isinstance(bind_dn, unicode):
            bind_dn = bind_dn.decode(self.api_encoding)

        return bind_dn.encode(self.ldap_encoding)


