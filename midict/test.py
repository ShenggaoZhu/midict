# -*- coding: utf-8 -*-
"""
Created on Sat Feb 20 11:32:37 2016

@author: shenggao
"""

import unittest
from hypothesis import assume, given, settings
from hypothesis.strategies import (
    binary, booleans, choices, dictionaries, floats, frozensets, integers,
    lists, none, recursive, text, tuples, sets)

from midict import MultiIndexDict

from math import isnan
from os import getenv


# https://groups.google.com/d/msg/hypothesis-users/8FVs--1yUl4/JEkJ02euEwAJ
settings.register_profile('default', settings(strict=True))
settings.load_profile(getenv('HYPOTHESIS_PROFILE', 'default'))


def inv(d):
    return {v: k for (k, v) in d.items()}


def prune_dup_vals(d):
    pruned = inv(inv(d))
    assume(len(pruned) >= len(d) // 2)
    return pruned


def both_nan(a, b):
    return isinstance(a, float) and isinstance(b, float) and \
            isnan(a) and isnan(b)


def eq_nan(a, b):
    return a == b or both_nan(a, b)


mutating_methods_by_arity = {
    0: (MultiIndexDict.clear, MultiIndexDict.popitem),
    1: (MultiIndexDict.__delitem__, MultiIndexDict.pop, MultiIndexDict.setdefault),
    2: (MultiIndexDict.__setitem__, MultiIndexDict.pop),
    -1: (MultiIndexDict.update),
}
# otherwise data gen. in hypothesis>=1.19 is so slow the health checks fail:
kw = dict(average_size=2)
immu_atom = none() | booleans() | integers() | floats() | text(**kw) | binary(**kw)
immu_coll = lambda e: frozensets(e, **kw) | lists(e, **kw).map(tuple)
immutable = recursive(immu_atom, immu_coll)
d = dictionaries(immutable, immutable, average_size=5).map(prune_dup_vals)

items_all = sets(immutable, average_size=30).map(list)
indices_names = sets(text(**kw), min_size=10, max_size=10).map(list)

dict_methods = set(dir({})) & set(dir(MultiIndexDict()))

class TestMIDict(unittest.TestCase):

    @given(d)
    def test_compat_dict(d):
        ''

#    @given(items_all, indices_names, integers(1,10))
#    def test_init(self, items_all, indices_names, n_idx):
##        items_all = list(items_all)
#        indices_names = indices_names[:n_idx]
#        N = len(items_all)
##        n_idx = 3
#        n_item = N // n_idx
#        items = []
#        for i in range(n_item):
#            items.append(items_all[i*n_idx:(i+1)*n_idx])
#        d = MultiIndexDict(items, indices_names)
#        print len(d),n_idx,  N #, indices_names



#
#
#@given(d)
#def test_len(d):
#    print d
#    b = MultiIndexDict(d)
#    assert len(b) == len(d)
#
##
##@given(d)
##def test_bidirectional_mappings(d):
##    b = MultiIndexDict(d)
##    for k, v in b.items():
##        assert eq_nan(k, b.inv[v])
#
#
## work around https://bitbucket.org/pypy/pypy/issue/1974
#nan = float('nan')
#WORKAROUND_NAN_BUG = (nan, nan) != (nan, nan)
#
#
#@given(d)
#def test_equality(d):
#    if WORKAROUND_NAN_BUG:
#        assume(nan not in d)
#    i = inv(d)
#    if WORKAROUND_NAN_BUG:
#        assume(nan not in i)
#    b = MultiIndexDict(d)
#    assert b == d
#    assert b.inv == i
#    assert not b != d
#    assert not b.inv != i
#
#
#@given(d, immutable, lists(tuples(immutable, immutable)))
#def test_consistency_after_mutation(d, arg, itemlist):
#    for arity, mms in mutating_methods_by_arity.items():
#        for mm in mms:
#            b = orderedMultiIndexDict(d) if 'orderedMultiIndexDict' in repr(mm) else MultiIndexDict(d)
#            args = []
#            if arity > 0:
#                args.append(arg)
#            if arity > 1:
#                args.append(arg)
#            if arity == -1:  # update and forceupdate
#                args.append(itemlist)
#            assert b == inv(b.inv)
#            assert b.inv == inv(b)
#            try:
#                mm(b, *args)
#            except:
#                pass
#            assert b == inv(b.inv)
#            assert b.inv == inv(b)

#class TestEncoding(unittest.TestCase):
#
#    @given(text())
#    def test_decode_inverts_encode(self, s):
#        print s
##        self.assertEqual(decode(encode(s)), s)
#
#


if __name__ == '__main__':
    ''
    unittest.main(verbosity=2)
#    test_len()