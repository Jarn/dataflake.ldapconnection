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
""" Utility functions and constants

$Id: utils.py 1485 2008-06-04 16:08:38Z jens $
"""

import ldap

BINARY_ATTRIBUTES = ('objectguid', 'jpegphoto')

def escape_dn(dn):
    """ Escape all characters that need escaping for a DN, see RFC 2253 
    """
    if dn is None:
        return None

    return ldap.dn.dn2str(ldap.dn.str2dn(dn))

