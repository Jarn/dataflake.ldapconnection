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
""" dummy: dummy test fixtures

$Id: dummy.py 1897 2010-02-06 13:27:07Z jens $
"""

ISO_8859_1_UNICODE = u'\xe4\xf6\xfc\xdf' # Umlauts a, o, u, sharp s
ISO_8859_1_UTF8 = ISO_8859_1_UNICODE.encode('UTF-8')
ISO_8859_1_ENCODED = ISO_8859_1_UNICODE.encode('iso-8859-1')
ISO_8859_7_UNICODE = u'\u03b1\u03b2\u03b3\u03b4' # Greek alpha beta gamma delta
ISO_8859_7_UTF8 = ISO_8859_7_UNICODE.encode('UTF-8')
ISO_8859_7_ENCODED = ISO_8859_7_UNICODE.encode('iso-8859-7')
