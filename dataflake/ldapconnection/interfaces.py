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
""" dataflake.ldapconnnection interfaces

$Id: interfaces.py 1889 2010-02-02 21:55:08Z jens $
"""

from zope.interface import Interface

class ILDAPConnection(Interface):
    """ ILDAPConnection interface

    ILDAPConnection instances provide a simplified way to talk to 
    a LDAP server. They allow defining one or more server connections 
    for automatic failover in case one LDAP server becomes unavailable.
    """

    def addServer(host, port, protocol, conn_timeout=-1, op_timeout=-1):
        """ Add a server definition

        `protocol` can be any one of ``ldap`` (unencrypted traffic), 
        ``ldaps`` (encrypted traffic to a separate port), ``ldaptls``
        (sets up encrypted traffic on the normal unencrypted port), or
        ``ldapi`` (trafic through a UNIX domain socket on the file system).

        The `conn_timeout` argument defines the number of seconds to wait
        until a new connection attempt is considered failed, which means 
        the next server is tried if it has been defined. -1 means 
        "wait indefinitely",

        The `op_timeout` argument defines the number of seconds to wait 
        until a LDAP server operation is considered failed, which means 
        the next server is tried if it has been defined. -1 means
        "wait indefinitely".

        If a server definition with a host, port and protocol that matches
        an existing server definition is added, the new values will replace
        the existing definition.
        """

    def removeServer(host, port, protocol):
        """ Remove a server definition

        Please note: I you remove the server definition of a server that 
        is currently being used, that connection will continue to be 
        used until it fails or until the Python process is restarted.
        """

    def connect(bind_dn=None, bind_pwd=None):
        """ Return a working LDAP server connection

        If no DN or password for binding to the LDAP server are passed in, 
        the DN and password configured into the LDAP connection instance 
        are used.

        The connection is cached and will be re-used. Since a bind operation
        is forced every time the method can be used to re-bind the cached
        connection with new credentials.

        This method returns an instance of the underlying `python-ldap` 
        connection class. It does not need to be called explicitly, all
        other operations call it implicitly.

        Raises RuntimeError if no server definitions are available.
        If all defined server connections fail the LDAP exception 
        thrown by the last attempted connection is re-raised.
        """

    def search( base
              , scope=2
              , fltr='(objectClass=*)'
              , attrs=None
              , convert_filter=True
              , bind_dn=None
              , bind_pwd=None
              ):
        """ Perform a LDAP search

        The search `base` is the point in the tree to search from. `scope`
        defines how to search and must be one of the scopes defined by the
        `python-ldap` module (`ldap.SCOPE_BASE`, `ldap.SCOPE_ONELEVEL` or
        `ldap.SCOPE_SUBTREE`). By default, `ldap.SCOPE_SUBTREE` is used.
        What to search for is described by the `filter` argument, which 
        must be a valid LDAP search filter string. If only certain record 
        attributes should be returned, they can be specified in the `attrs` 
        sequence.

        If the search raised no errors, a mapping with the following keys
        is returned:

        - results: A sequence of mappings representing a matching record

        - size: The number of matching records

        The results sequence itself contains mappings that have a `dn` key
        containing the full distinguished name of the record, and key/values
        representing the records' data as returned by the LDAP server.

        In order to perform the operation using credentials other than the
        credentials configured on the instance a DN and password may be
        passed in.
        """

    def insert(base, rdn, attrs=None, bind_dn=None, bind_pwd=None):
        """ Insert a new record 

        The record will be inserted at `base` with the new RDN `rdn`.
        `attrs` is expected to be a key:value mapping where the value may 
        be a string or a sequence of strings. 
        Multiple values may be expressed as a single string if the values 
        are semicolon-delimited.
        Values can be marked as binary values, meaning they are not encoded
        in the encoding specified as the server encoding before being sent 
        to the LDAP server, by appending ';binary' to the key.

        In order to perform the operation using credentials other than the
        credentials configured on the instance a DN and password may be
        passed in.
        """

    def delete(dn, bind_dn=None, bind_pwd=None):
        """ Delete the record specified by the given DN

        In order to perform the operation using credentials other than the
        credentials configured on the instance a DN and password may be
        passed in.
        """

    def modify(dn, mod_type=None, attrs=None, bind_dn=None, bind_pwd=None):
        """ Modify the record specified by the given DN

        `mod_type` is one of the LDAP modification types as declared by
        the `python-ldap`-module, such as `ldap.MOD_ADD`, 
        PUrl(urlscheme=protocol, hostport=hostport)
        provided, the modification type is guessed by comparing the 
        current record with the `attrs` mapping passed in.

        `attrs` is expected to be a key:value mapping where the value may 
        be a string or a sequence of strings. 
        Multiple values may be expressed as a single string if the values 
        are semicolon-delimited.
        Values can be marked as binary values, meaning they are not encoded
        as UTF-8 before sending the to the LDAP server, by appending 
        ';binary' to the key.

        In order to perform the operation using credentials other than the
        credentials configured on the instance a DN and password may be
        passed in.
        """

