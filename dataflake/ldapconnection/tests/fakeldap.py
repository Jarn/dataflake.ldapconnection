##############################################################################
#
# Copyright (c) 2000-2009 Jens Vagelpohl and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" A fake LDAP module for unit tests

$Id: FakeLDAP.py 1485 2008-06-04 16:08:38Z jens $
"""

import base64
import copy
try:
    from hashlib import sha1 as sha_new
except ImportError:
    from sha import new as sha_new
import ldap
from ldap.dn import explode_dn
import re

# From http://www.ietf.org/rfc/rfc2254.txt, Section 4
#
# filter     = "(" filtercomp ")"
# filtercomp = and / or / not / item
# and        = "&" filterlist
# or         = "|" filterlist
# not        = "!" filter
# filterlist = 1*filter
# item       = simple / present / substring / extensible
# simple     = attr filtertype value
# filtertype = equal / approx / greater / less
# equal      = "="
# approx     = "~="
# greater    = ">="
# less       = "<="
# extensible = attr [":dn"] [":" matchingrule] ":=" value
#              / [":dn"] ":" matchingrule ":=" value
# present    = attr "=*"
# substring  = attr "=" [initial] any [final]
# initial    = value
# any        = "*" *(value "*")
# final      = value
# attr       = AttributeDescription from Section 4.1.5 of [1]
# matchingrule = MatchingRuleId from Section 4.1.9 of [1]
# value      = AttributeValue from Section 4.1.6 of [1]


_FLTR = r'\(\w*?=[\*\w\s=,\\]*?\)'
_OP = '[&\|\!]{1}'

FLTR = r'\((?P<attr>\w*?)(?P<comp>=)(?P<value>[\*\w\s=,\\\']*?)\)'
FLTR_RE = re.compile(FLTR + '(?P<fltr>.*)')

OP = '\((?P<op>(%s))(?P<fltr>(%s)*)\)' % (_OP, _FLTR)
FULL = '\((?P<op>(%s))(?P<fltr>.*)\)' % _OP

OP_RE = re.compile(OP)
FULL_RE = re.compile(FULL)

class Op(object):

    def __init__(self, op):
        self.op = op

    def __repr__(self):
        return "Op('%s')" % self.op

class Filter(object):
    """ A simple representation for search filter elements
    
    >>> fltr = Filter('cn', '=', 'joe')
    >>> repr(fltr)
    "Filter('cn', '=', 'joe')"
    >>> fltr == Filter('cn', '=', 'joe')
    True
    >>> fltr == Filter('CN', '=', 'joe')
    True
    >>> fltr == Filter('cn', '=', 'Joe')
    False
    >>> filters = [Filter('CN', '=', 'Zack'), Filter('cn', '=', 'Fred')]
    >>> filters.sort()
    >>> filters
    [Filter('cn', '=', 'Fred'), Filter('CN', '=', 'Zack')]
    """

    def __init__(self, attr, comp, value):
        self.attr = attr
        self.comp = comp
        self.value = value

    def __repr__(self):
        return "Filter('%s', '%s', '%s')" % (self.attr, self.comp, self.value)

    def __cmp__(self, other):
        return cmp((self.attr.lower(), self.comp, self.value),
                   (other.attr.lower(), other.comp, other.value))

    def __eq__(self, other):
        v1 = (self.attr.lower(), self.comp, self.value)
        v2 = (other.attr.lower(), other.comp, other.value)
        return v1 == v2

def parse_query(query, recurse=False):
    """
    >>> parse_query('(&(objectclass=person)(cn=jhunter*))')
    (Op('&'), (Filter('objectclass', '=', 'person'), Filter('cn', '=', 'jhunter*')))

    >>> parse_query('(&(objectclass=person)(|(cn=Jeff Hunter)(cn=mhunter*)))')
    (Op('&'), (Filter('objectclass', '=', 'person'), (Op('|'), (Filter('cn', '=', 'Jeff Hunter'), Filter('cn', '=', 'mhunter*')))))

    >>> parse_query('(&(l=USA)(!(sn=patel)))')
    (Op('&'), (Filter('l', '=', 'USA'), (Op('!'), (Filter('sn', '=', 'patel'),))))

    >>> parse_query('(!(&(drink=beer)(description=good)))')
    (Op('!'), (Op('&'), (Filter('drink', '=', 'beer'), Filter('description', '=', 'good'))))

    >>> parse_query('(&(objectclass=person)(dn=cn=jhunter,dc=dataflake,dc=org))')
    (Op('&'), (Filter('objectclass', '=', 'person'), Filter('dn', '=', 'cn=jhunter,dc=dataflake,dc=org')))

    >>> from pprint import pprint
    >>> q = parse_query('(|(&(objectClass=group)(member=cn=test,ou=people,dc=dataflake,dc=org))'
    ...                 '(&(objectClass=groupOfNames)(member=cn=test,ou=people,dc=dataflake,dc=org))'
    ...                 '(&(objectClass=groupOfUniqueNames)(uniqueMember=cn=test,ou=people,dc=dataflake,dc=org))'
    ...                 '(&(objectClass=accessGroup)(member=cn=test,ou=people,dc=dataflake,dc=org)))')

    >>> pprint(q)
    (Op('|'),
     (Op('&'),
      (Filter('objectClass', '=', 'group'),
       Filter('member', '=', 'cn=test,ou=people,dc=dataflake,dc=org')),
      Op('&'),
      (Filter('objectClass', '=', 'groupOfNames'),
       Filter('member', '=', 'cn=test,ou=people,dc=dataflake,dc=org')),
      Op('&'),
      (Filter('objectClass', '=', 'groupOfUniqueNames'),
       Filter('uniqueMember', '=', 'cn=test,ou=people,dc=dataflake,dc=org')),
      Op('&'),
      (Filter('objectClass', '=', 'accessGroup'),
       Filter('member', '=', 'cn=test,ou=people,dc=dataflake,dc=org'))))
    """
    parts = []
    for expr in (OP_RE, FULL_RE):
        # Match outermost operations
        m = expr.match(query)
        if m:
            d = m.groupdict()
            op = Op(d['op'])
            sub = parse_query(d['fltr'])
            if recurse:
                parts.append((op, sub))
            else:
                parts.append(op)
                parts.append(sub)
            rest = query[m.end():]
            if rest:
                parts.extend(parse_query(rest))
            return tuple(parts)

    # Match internal filter.
    m = FLTR_RE.match(query)
    if m is None:
        raise ValueError(query)
    d = m.groupdict()
    parts.append(Filter(d['attr'], d['comp'], d['value']))
    if d['fltr']:
        parts.extend(parse_query(d['fltr'], recurse=True))
    return tuple(parts)

def flatten_query(query, klass=Filter):
    """
    >>> q = parse_query('(&(objectclass=person)(|(cn=Jeff Hunter)(cn=mhunter*)))')

    >>> flatten_query(q, Filter)
    (Filter('objectclass', '=', 'person'), Filter('cn', '=', 'Jeff Hunter'), Filter('cn', '=', 'mhunter*'))

    >>> flatten_query(q, Op)
    (Op('&'), Op('|'))
    """
    q = [f for f in query if isinstance(f, klass)]
    for item in query:
        if isinstance(item, tuple):
            q.extend(flatten_query(item, klass))
    return tuple(q)

def explode_query(query):
    """
    >>> q = parse_query('(&(objectClass=person)(|(cn=Jeff Hunter)(cn=mhunter*)))')
    >>> for sub in explode_query(q):
    ...     print sub
    (Op('|'), (Filter('cn', '=', 'Jeff Hunter'), Filter('cn', '=', 'mhunter*')))
    (Op('&'), (Filter('objectClass', '=', 'person'),))

    >>> q = parse_query('(objectClass=*)')
    >>> for sub in explode_query(q):
    ...     print sub
    (Op('&'), (Filter('objectClass', '=', '*'),))

    >>> from pprint import pprint
    >>> q = parse_query('(|(&(objectClass=group)(member=cn=test,ou=people,dc=dataflake,dc=org))'
    ...                   '(&(objectClass=groupOfNames)(member=cn=test,ou=people,dc=dataflake,dc=org))'
    ...                   '(&(objectClass=groupOfUniqueNames)(uniqueMember=cn=test,ou=people,dc=dataflake,dc=org))'
    ...                   '(&(objectClass=accessGroup)(member=cn=test,ou=people,dc=dataflake,dc=org)))')
    >>> for sub in explode_query(q):
    ...     pprint(sub)
    (Op('&'),
     (Filter('objectClass', '=', 'group'),
      Filter('member', '=', 'cn=test,ou=people,dc=dataflake,dc=org')))
    (Op('&'),
     (Filter('objectClass', '=', 'groupOfNames'),
      Filter('member', '=', 'cn=test,ou=people,dc=dataflake,dc=org')))
    (Op('&'),
     (Filter('objectClass', '=', 'groupOfUniqueNames'),
      Filter('uniqueMember', '=', 'cn=test,ou=people,dc=dataflake,dc=org')))
    (Op('&'),
     (Filter('objectClass', '=', 'accessGroup'),
      Filter('member', '=', 'cn=test,ou=people,dc=dataflake,dc=org')))
    (Op('|'), ())
    """
    if isinstance(query, str):
        query = parse_query(query)

    res = []
    def dig(sub, res):
        level = []
        for item in sub:
            if isinstance(item, tuple):
                got = dig(item, res)
                if got and level and isinstance(level[0], Op):
                    level.append(got)
                    res.append(tuple(level))
                    level = []
            else:
                level.append(item)
        return tuple(level)

    level = dig(query, res)
    if not res:
        # A simple filter with no operands
        return ((Op('&'), level),)
    if level:
        # Very likely a single operand around a group of filters.
        assert len(level) == 1, (len(level), level)
        res.append((level[0], ()))
    return tuple(res)

def cmp_query(query, other, strict=False):
    """
    >>> print cmp_query('(&(objectclass=person)(cn=jhunter*))', '(objectClass=person)')
    Filter('objectClass', '=', 'person')

    >>> print cmp_query('(&(objectClass=groupOfUniqueNames)(uniqueMember=sidnei))', '(objectClass=groupOfUniqueNames)')
    Filter('objectClass', '=', 'groupOfUniqueNames')

    >>> print cmp_query('(&(objectClass=groupOfUniqueNames)(uniqueMember=sidnei))', '(uniqueMember=sidnei)')
    Filter('uniqueMember', '=', 'sidnei')

    >>> print cmp_query('(&(objectClass=groupOfUniqueNames)(uniqueMember=sidnei))', '(uniqueMember=jens)')
    None
    """
    if isinstance(query, str):
        query = parse_query(query)
    if isinstance(other, str):
        other = parse_query(other)

    q1 = flatten_query(query)
    q2 = flatten_query(other)

    if strict:
        return q1 == q2

    for fltr in q2:
        if fltr in q1:
            return fltr

def find_query_attr(query, attr):
    """
    >>> print find_query_attr('(&(objectclass=person)(cn=jhunter*))', 'objectClass')
    Filter('objectclass', '=', 'person')

    >>> print find_query_attr('(&(objectClass=groupOfUniqueNames)(uniqueMember=sidnei))', 'uniqueMember')
    Filter('uniqueMember', '=', 'sidnei')

    >>> print find_query_attr('(&(objectClass=groupOfUniqueNames)(uniqueMember=sidnei))', 'cn')
    None
    """
    if isinstance(query, str):
        query = parse_query(query)

    q1 = flatten_query(query)

    for fltr in q1:
        if fltr.attr.lower() == attr.lower():
            return fltr

TREE = {}

ANY = parse_query('(objectClass=*)')
GROUP_OF_UNIQUE_NAMES = parse_query('(objectClass=groupOfUniqueNames)')


def clearTree():
    TREE.clear()

def addTreeItems(dn):
    """ Add structure directly to the tree given a DN 

    returns the last added tree position for convenience
    """
    elems = explode_dn(dn)
    elems.reverse()
    tree_pos = TREE

    for elem in elems:
        if not tree_pos.has_key(elem):
            tree_pos[elem] = {}

        tree_pos = tree_pos[elem]

    return tree_pos

def apply_filter(tree_pos, base, fltr):
    res = []
    q_key, q_val = fltr.attr, fltr.value
    wildcard = False
    if q_val.startswith('*') or q_val.endswith('*'):
        if q_val != '*':
            # Wildcard search
            if q_val.startswith('*') and q_val.endswith('*'):
                wildcard = 'both'
                q_val = q_val[1:-1]
            elif q_val.startswith('*'):
                wildcard = 'start'
                q_val = q_val[1:]
            elif q_val.endswith('*'):
                wildcard = 'end'
                q_val = q_val[:-1]
    # Need to find out if tree_pos is a leaf record, it needs different handling
    # Leaf records will appear when doing BASE-scoped searches.
    if tree_pos.has_key('dn'):
        key = explode_dn(tree_pos['dn'])[0]
        to_search = [(key, tree_pos)]
    else:
        to_search = tree_pos.items()

    for key, val in to_search:
        found = True
        if val.has_key(q_key):
            if q_val == '*':
                # Always include if there's a value for it.
                pass
            elif wildcard:
                found = False
                for x in val[q_key]:
                    if wildcard == 'start':
                        if x.endswith(q_val):
                            found = True
                            break
                    elif wildcard == 'end':
                        if x.startswith(q_val):
                            found = True
                            break
                    else:
                        if q_val in x:
                            found = True
                            break
            elif not q_val in val[q_key]:
                found = False
            if found:
                res.append(('%s,%s' % (key, base), val))
    return res

class FakeLDAPConnection:

    def __init__(self, *args, **kw):
        self.args = args
        self.kwargs = kw
        self.options = {}
        self._last_bind = None
        self.start_tls_called = False

    def set_option(self, option, value):
        self.options[option] = value

    def simple_bind_s(self, binduid, bindpwd):
        self._last_bind = (self.simple_bind_s, (binduid, bindpwd), {})

        if binduid.find('Manager') != -1:
            return 1

        if bindpwd == '':
            # Emulate LDAP mis-behavior
            return 1

        sha_obj = sha_new(bindpwd)
        sha_dig = sha_obj.digest()
        enc_bindpwd = '{SHA}%s' % base64.encodestring(sha_dig)
        enc_bindpwd = enc_bindpwd.strip()
        rec = self.search_s(binduid)
        rec_pwd = ''
        for key, val_list in rec:
            if key == 'userPassword':
                rec_pwd = val_list[0]
                break

        if not rec_pwd:
            raise ldap.INVALID_CREDENTIALS

        if enc_bindpwd == rec_pwd:
            return 1
        else:
            raise ldap.INVALID_CREDENTIALS

    def search_s(self, base, scope=ldap.SCOPE_SUBTREE,
                 query='(objectClass=*)', attrs=()):

        elems = explode_dn(base)
        elems.reverse()
        tree_pos = TREE
        tree_pos_dn = ''

        for elem in elems:
            if not tree_pos_dn:
                tree_pos_dn = elem
            else:
                tree_pos_dn = '%s,%s' % (elem, tree_pos_dn)
            if tree_pos.has_key(elem):
                tree_pos = tree_pos[elem]
            else:
                raise ldap.NO_SUCH_OBJECT(elem)

        q = parse_query(query)

        if cmp_query(q, ANY, strict=True):
            # Return all objects, no matter what class
            if scope == ldap.SCOPE_BASE and tree_pos_dn == base:
                # Only if dn matches 'base'
                return (([base, tree_pos],))
            else:
                return tree_pos.items()

        by_level = {}
        for idx, (operation, filters) in enumerate(explode_query(q)):
            lvl = by_level[idx] = []
            by_filter = {}
            for fltr in filters:
                sub = apply_filter(tree_pos, base, fltr)
                by_filter[fltr] = sub
                # Optimization: If it's an AND query bail out on
                # the first empty value, but still set the empty
                # value on by_filter so it gets caught in the
                # operations below.
                if not sub and operation.op in ('&',):
                    break

            if filters:
                values = by_filter.values()
            else:
                # If there are no filters, it's an operation on
                # all the previous levels.
                values = by_level.values()

            if operation.op in ('|',):
                # Do an union
                lvl_vals = dict(lvl)
                lvl_keys = set(lvl_vals.keys())
                for sub in values:
                    sub_vals = dict(sub)
                    sub_keys = set(sub_vals.keys())
                    for k in sub_keys - lvl_keys:
                        lvl.append((k, sub_vals[k]))
                    lvl_keys = sub_keys | lvl_keys
            elif operation.op in ('&',):
                # Do an intersection
                for sub in values:
                    # Optimization: If it's an AND query bail out on
                    # the first empty value.
                    if not sub:
                        lvl[:] = []
                        break
                    if not lvl:
                        lvl[:] = sub
                    else:
                        new_lvl = []
                        lvl_vals = dict(lvl)
                        sub_vals = dict(sub)
                        lvl_keys = set(lvl_vals.keys())
                        sub_keys = set(sub_vals.keys())
                        for k in sub_keys & lvl_keys:
                            new_lvl.append((k, lvl_vals[k]))
                        lvl[:] = new_lvl
        if by_level:
            # Return the last one.
            return by_level[idx]

        return []


    def add_s(self, dn, attr_list):
        elems = explode_dn(dn)
        elems.reverse()
        rdn = elems[-1]
        base = elems[:-1]
        tree_pos = TREE

        for elem in base:
            if tree_pos.has_key(elem):
                tree_pos = tree_pos[elem]
            else:
                raise ldap.NO_SUCH_OBJECT(elem)

        if tree_pos.has_key(rdn):
            raise ldap.ALREADY_EXISTS(rdn)

        # Add rdn to attributes as well.
        k, v = rdn.split('=')
        tree_pos[rdn] = {k:[v]}
        rec = tree_pos[rdn]

        for key, val in attr_list:
            rec[key] = val


    def delete_s(self, dn):
        elems = explode_dn(dn)
        elems.reverse()
        rdn = elems[-1]
        base = elems[:-1]
        tree_pos = TREE

        for elem in base:
            if tree_pos.has_key(elem):
                tree_pos = tree_pos[elem]
            else:
                raise ldap.NO_SUCH_OBJECT(elem)

        if not tree_pos.has_key(rdn):
            raise ldap.NO_SUCH_OBJECT(rdn)

        del tree_pos[rdn]

    def modify_s(self, dn, mod_list):
        elems = explode_dn(dn)
        elems.reverse()
        rdn = elems[-1]
        base = elems[:-1]
        tree_pos = TREE

        for elem in base:
            if tree_pos.has_key(elem):
                tree_pos = tree_pos[elem]
            else:
                raise ldap.NO_SUCH_OBJECT(elem)

        if not tree_pos.has_key(rdn):
            raise ldap.NO_SUCH_OBJECT(rdn)

        rec = copy.deepcopy(tree_pos.get(rdn))

        for mod in mod_list:
            if mod[0] == ldap.MOD_REPLACE:
                rec[mod[1]] = mod[2]
            elif mod[0] == ldap.MOD_ADD:
                cur_val = rec.get(mod[1], [])
                cur_val.extend(mod[2])
                rec[mod[1]] = cur_val
            else:
                if rec.has_key(mod[1]):
                    if mod[2] is None:
                        del rec[mod[1]]
                    else:
                        cur_vals = rec[mod[1]]
                        for removed in mod[2]:
                            if removed in cur_vals:
                                cur_vals.remove(removed)

                        rec[mod[1]] = cur_vals

        tree_pos[rdn] = rec

    def modrdn_s(self, dn, new_rdn, *ign):
        elems = explode_dn(dn)
        elems.reverse()
        rdn = elems[-1]
        base = elems[:-1]
        tree_pos = TREE

        for elem in base:
            if tree_pos.has_key(elem):
                tree_pos = tree_pos[elem]
            else:
                raise ldap.NO_SUCH_OBJECT(elem)

        if not tree_pos.has_key(rdn):
            raise ldap.NO_SUCH_OBJECT(rdn)

        if tree_pos.has_key(new_rdn):
            raise ldap.ALREADY_EXISTS(new_rdn)

        rec = tree_pos.get(rdn)

        del tree_pos[rdn]
        tree_pos[new_rdn] = rec

    def start_tls_s(self):
        self.start_tls_called = True

    def result(self, msgid=ldap.RES_ANY, all=1, timeout=-1):
        return ('partial', [('partial result', {'dn': 'partial result'})])

    def unbind(self):
        pass


class RaisingFakeLDAPConnection(FakeLDAPConnection):

    def setExceptionAndMethod(self, raise_on, exc_class, exc_arg=None):
        hideaway = '%s_old' % raise_on
        setattr(self, hideaway, getattr(self, raise_on))
        def func(*args, **kw):
            setattr(self, raise_on, getattr(self, hideaway))
            setattr(self, 'args', args)
            setattr(self, 'kwargs', kw)
            if exc_arg:
                raise exc_class(exc_arg)
            else:
                raise exc_class
        setattr(self, raise_on, func)


class FixedResultFakeLDAPConnection(FakeLDAPConnection):
    search_results = []

    def search_s( self, base, scope=ldap.SCOPE_SUBTREE,
                  query='(objectClass=*)', attrs=() ):
        return self.search_results


class ldapobject:
    class ReconnectLDAPObject(FakeLDAPConnection):
        pass
