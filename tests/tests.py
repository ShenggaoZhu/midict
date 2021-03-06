# -*- coding: utf-8 -*-
"""
Created on Wed Apr 20 11:13:35 2016

@author: Shenggao
"""
from __future__ import absolute_import, division, print_function #, unicode_literals

import unittest
from collections import OrderedDict
import pickle

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from midict import *
from midict import PY2, PY3 # not in midict.__all__
if PY3:
    from midict import map


def call(obj, func_name, *args, **kw):
    'call function by `func_name` of obj'
    func = getattr(obj, func_name)
    return func(*args, **kw)


class EasyArg(object):
    '''
    Easily obtain the argument (e.g., slice) of __getitem__() via the bracket syntax.
    Easily obtain the *arg and **kw from function calls.

    _s = EasyArg()
    _s[1:] -> slice(1, None, None)
    _s['a':1,'b'] -> (slice('a', 1, None), 'b')

    _s(1,2,a=5) -> ((1, 2), {'a': 5})
    '''
    def __getitem__(self, arg):
        return arg

    def __call__(self, *arg, **kw):
        return arg, kw

_s = EasyArg()


def get_data3(cls=MIDict):
    items = [['jack', 1, (192,1)],
             ['tony', 2, (192,2)],
             ['alice', 3, (192,3)]]
    names = ['name', 'uid', 'ip']
    d = cls(items, names)
    return d, items, names

# run command line:
# !coverage run tests/tests.py;coverage report;coverage html
# !coverage run --source midict tests/tests.py;coverage report;coverage html

#==============================================================================
# test cases
#==============================================================================

class TestBasic(unittest.TestCase):
    def test_od_replace_key(self):
        keys0 = list(range(10))
        od0 = OrderedDict.fromkeys(keys0)

        keys = list(keys0)
        i = 5 # single
        i2 = 50
        value = 'new value'
        keys[i] = i2
        od = od0.copy()
        od_replace_key(od, i, i2, value)
        self.assertEqual(list(od.keys()), keys)
        self.assertEqual(od[i2], value)

        keys = list(keys0)
        i = 5 # single
        i2 = 6 # overwrite
        keys.remove(i2)
        keys[i] = i2
        od = od0.copy()
        od_replace_key(od, i, i2)
        self.assertEqual(list(od.keys()), keys)

        keys = list(keys0)
        i = [5, 6] # multi
        i2 = [50, 60]
        value = ['new value 1', 'new value 2']
        mset_list(keys, i, i2)
        od = od0.copy()
        od_replace_key(od, i, i2, value)
        self.assertEqual(list(od.keys()), keys)
        for k,v in zip(i2, value):
            self.assertEqual(od[k], v)

        with self.assertRaises(ValueError):
            od_replace_key(od, [1], [1,2]) # len not equal

        with self.assertRaises(ValueError):
            od_replace_key(od, [1], [10], [1, 2]) # len not equal

    def test_od_reorder_keys(self):
        keys = list(range(10))
        od = OrderedDict.fromkeys(keys)
        keys2 = keys[::-1]
        od_reorder_keys(od, keys2)
        self.assertEqual(list(od.keys()), keys2)

        with self.assertRaises(KeyError):
            od_reorder_keys(od, [])

    def test_convert_dict(self):
        d0 = {1:{1:1}, 2:[{2:2}]}
#        ad = AttrDict({1:AttrDict({1:1}), 2:[AttrDict({2:2})]})
        d = convert_dict(d0, AttrDict)
        self.assertIsInstance(d, AttrDict)
        self.assertIsInstance(d[1], AttrDict)
        self.assertIsInstance(d[2][0], AttrDict)


    def test_AttrDict(self):
        d = AttrDict()
        self.assertTrue(hasattr(d, '_AttrDict__attr2item'))

        d.a = 1
        d.b = 2
        delattr(d, 'a')
        del d['b']
        self.assertEqual(d, AttrDict())
        delattr(d, '_AttrDict__attr2item')


    def test_IndexDict(self):
        names = ['name', 'uid', 'ip']
        N = len(names)
        d = IndexDict(zip(names, range(N)), name='jack') # overwrite

        names_not_exist = get_unique_name('', names)

        self.assertEqual(d['name'], 'jack')

        d[:] = [None] * N
        self.assertEqual(d[:], [None] * N)

        paras = []
        paras.append(N+10)
        paras.append(names_not_exist)
        paras.append(_s[names_not_exist:])
        paras.append(_s[:names_not_exist])

        for para in paras:
            with self.assertRaises(KeyError):
                d[para]

        with self.assertRaises(ValueError):
            d[:] = [None] * (N + 10) # len not equal

        for key in [None, 0, (1,2)]: # not allowed key types
            with self.assertRaises(TypeError):
                IndexDict([[key, 1]])

        # not allowed key types
        with self.assertRaises(TypeError):
            d[None] = 1

        del d['name']
        del d[:]
        self.assertEqual(d, IndexDict())


    def test_ValueExistsError(self):
        for cls in [KeyError, MIMappingError, Exception]:
            self.assertTrue(issubclass(ValueExistsError, cls))
        value, index_order, index_name = 'jack', 1, 'name'
        e = ValueExistsError(value, index_order, index_name)
        str(e) # no error



class TestMIMapping(unittest.TestCase):

    def test_init(self):
        data = []
        N_items = 3
        for k_indices in [2, 3, 9]: # number of indices
            items = []
            for n in range(N_items):
                item = tuple([i+n for i in range(k_indices)]) # populate values
                items.append(item)
            names = map(str, range(k_indices))
            data.append([items, names])

        for items, names in data:
            for n in [names, ''.join(names)]: # single str '012'
                d1 = MIDict(items, names)
                d2 = MIDict(iter(items), iter(names))

                ds = [d1, d2]
                if PY2: # zip is iter
                    d3 = MIDict(d1.viewitems(), iter(names))
                    ds += [d3]
                else:
                    cols = list(zip(*items))
                    d4 = MIDict(zip(*cols), names)
                    ds += [d4]

                for d in ds:
                    self.assertEqual(list(d.indices.keys()), names)
                    self.assertEqual(force_list(d.items()), items)

        d = MIDict(items, names)
        d2 = MIDict(d)
        self.assertEqual(d2, d)

        dct = dict(a=1, b=2, c=3)
        d2 = MIDict(dct)
        self.assertEqual(d2, dct)

        d2 = MIDict(**dct)
        self.assertEqual(d2, dct)

        class ItemObj(object):
            items = dct.items # callable item()

        obj = ItemObj()
        d2 = MIDict(obj)
        self.assertEqual(d2, dct)

        class ListObj(list):
            pass
        items_list = ListObj(dct.items())
        items_list.items = None # not callable item
        d2 = MIDict(items_list)
        self.assertEqual(d2, dct)


    def test_init_error(self):
        d, items, names = get_data3()
        names_dup = ['name', 'ip', 'ip']
        names_int = list(range(3))
        names2 = names * 2
        items2 = items + [[1]]

        paras = []
        paras.append([_s(items, names, []), TypeError])
        paras.append([_s(items2, names), ValueError])
        paras.append([_s(items, names2), ValueError])
        paras.append([_s(items, names, a=1), ValueError])
        paras.append([_s(items, names_dup), ValueError])
        paras.append([_s(items, names_int), TypeError])


        for (arg, kw), err in paras:
            with self.assertRaises(err):
                MIDict(*arg, **kw)


    def test_single_index(self):
        items = [[i] for i in range(5)]
        names = ['index']
        d = MIDict(items, names)
        for i in range(5):
            self.assertEqual(d[i], i)
            self.assertEqual(d[0:i], i)
            self.assertEqual(d['index':i], i)

    def test_mutable_methods(self):
        d, items, names = get_data3(MIMapping)
        key = items[0][0]
        with self.assertRaises(NotImplementedError):
            d[key] =[0, 1]

        with self.assertRaises(NotImplementedError):
            del d[key]

        with self.assertRaises(NotImplementedError):
            d.clear()

        with self.assertRaises(NotImplementedError):
            d.update()


    def test_fromkeys(self):
        for cls in [MIMapping, MIDict, FrozenMIDict]:
            for keys in [[], [1]]:
                for value in [None, 0]:
                    for names in [None, ['a', 'b']]:
                        d = cls.fromkeys(keys, value, names)
                        self.assertEqual(d.__class__, cls)
                        self.assertEqual(list(d.keys()), keys)
                        self.assertEqual(list(d.values()), [value for k in keys])
                        if keys:
                            if names is None:
                                names = ['index_1', 'index_2']
                            self.assertEqual(list(d.indices.keys()), names)

        with self.assertRaises(ValueError):
            MIMapping.fromkeys([1,2,3])




class TestFrozenMIDict(unittest.TestCase):
    def test_convert(self):
        for cls in [MIMapping, MIDict]:
            d, items, names = get_data3(cls)
            for df in [FrozenMIDict(items, names), FrozenMIDict(d)]:
                self.assertEqual(d, df)

    def test_hash(self):
        d, items, names = get_data3(FrozenMIDict)
        {d:d}
        set([d, d])


#==============================================================================
# test MIDict
#==============================================================================


class TestMIDict_3_Indices(unittest.TestCase):

    def get_data(self, cls=MIDict):
        items = [['jack', 1, (192,1)],
#                 ['tony', 2, (192,2)],
                 ['alice', 3, (192,3)]]
        names = ['name', 'uid', 'ip']
        d =  cls(items, names)
        return d, items, names

    def test_getitem(self):
        d, items, names = self.get_data()
        N = len(names)
        for item in items:
            # d[index1:key, index2] == val
            index2_list = [] # variable index2 args

            # index2: single value
            for k in range(N):
                index2_list.append(k)

            # index2: multi values
            index2_list.append(list(range(N)))
            index2_list.append(_s[:])

            index2_list.append(list(range(N))*2)  # any duplicate names

            # d[index1:key, index2_1, index2_2, ...]
            index2_list.append(tuple(range(N)))

            index2_list.append(_s[::2])
            index2_list.append(list(range(0, N, 2)))
            index2_list.append(_s[:N+10])

            index2_list.append(_s[1:])
            index2_list.append(_s[:1])
            index2_list.append(_s[0:-1])

            index2_list.append([])
            index2_list.append(_s[0:0])

            index2_val_comb = [] # variable index2 args and resulting val
            for index2 in index2_list:
                val = mget_list(item, index2)
                if isinstance(index2, int):
                    index2_val_comb.append([index2, val])
                    index2_val_comb.append([-N+index2, val])
                    index2_val_comb.append([names[index2], val])

                elif isinstance(index2, list):
                    mixed_name = [names[index2[k]] if k%2 else index2[k] for k in range(len(index2))]
                    all_name = mget_list(names, index2)
                    all_neg = [-N+i if i >=0 else i for i in index2]
                    for arr in (index2, mixed_name, all_name, all_neg):
                        index2_val_comb.append([arr, val])
                        index2_val_comb.append([tuple(arr), val])

                elif isinstance(index2, tuple):
                    mixed_name = [names[index2[k]] if k%2 else index2[k] for k in range(len(index2))]
                    all_name = mget_list(names, index2)
                    all_neg = [-N+i if i >=0 else i for i in index2]
                    for arr in (list(index2), mixed_name, all_name, all_neg):
                        index2_val_comb.append(arr + [val])

                elif isinstance(index2, slice):
                    start_top_arr = [[], []]
                    for k, arr in zip([index2.start, index2.stop], start_top_arr):
                        arr.append(k)
                        if isinstance(k, int) and -N <= k < N:
                            arr.append(names[k])
                    step = index2.step
                    for start in start_top_arr[0]:
                        for stop in start_top_arr[1]:
                            index2_val_comb.append([_s[start : stop : step], val])

            for i, (index1, key) in enumerate(zip(names, item)):
                # all possible syntax for [index1:key] part
                args = []
                args.append(_s[index1: key])
                args.append(_s[i: key])
                args.append(_s[-N+i: key])
                if i == 0:
                    args.append(key)
                if i == N-1:
                    args.append(_s[:key])

                # d[index1:key] == value
                value = [v for v in item if v != key]
                if len(value) == 1:
                    value = value[0]

                index2_val_all= list(index2_val_comb) # copy

                # no index2, d[index1:key] == value
                index2_val_all.append([value])

                for arg in args:
                    for row in index2_val_all:
                        val = row[-1]
                        index2 = row[:-1] # maybe 0, 1 or more
                        paras = []
                        if len(index2) == 0:
                            paras.append(arg)
                            # add a comma after arg only when arg is a slice
                            if isinstance(arg, slice):
                                paras.append((arg,))
                        else:
                            paras.append(tuple([arg] + index2))

                        for para in paras:
                            if not isinstance(arg, slice) and len(row) > 1:
                                # d[key, name], d[key, i], d[key, tuple] or d[key, k1, k2...] not working
                                if (len(para) == 2 and not isinstance(para[1], (list, slice))) or len(para) > 2:
                                    with self.assertRaises(KeyError):
                                        d[para]
                                    continue

                            self.assertEqual(d[para], val,
                                '%r :not equal: d[%r] = %r' % (val, para, d[para]))


    def test_getitem_error(self):
        d, items, names = self.get_data()
        N = len(names)
        M1 = N + 10 # out of range
        M2 = -N - 10

        index_exist = names[0]
        index_not_exist = get_unique_name('', names)
        key_exist = list(d.keys())[0]
        key_not_exist = get_unique_name('', d)

        # d[index_exist:key_exist] is valid
        d[index_exist:key_exist]

        paras = []
        for index1 in [index_not_exist, M1, M2]: # index not exist
            for key in [key_exist, key_not_exist]:
                paras.append(_s[index1:key])

        for index1 in [index_exist, 0]:
            paras.append(_s[index1: key_not_exist]) # only key not exist

        arg_exist = _s[index_exist: key_exist]
        for index2 in [index_not_exist, M1, M2]: # index2 not exist
            paras.append((arg_exist, index2))
            for index2_exist in [index_exist, 0]:
                paras.append((arg_exist, [index2, index2_exist]))
                paras.append((arg_exist, index2, index2_exist))
                # extra arg after index2
                paras.append((key_exist, [index2_exist], index2))
                paras.append((arg_exist, [index2_exist], index2))
                paras.append((arg_exist, [index2, index2_exist], index2))


        for para in paras:
            with self.assertRaises(KeyError):
                d[para]



    def test_setitem_nonempty(self):
        # modify existing items, construct a new MIDict, and compare with results of setitem
        d, items, names = self.get_data()
        N = len(names)
        L = len(items)

        # cached signature and d_new
        cache_sign = []
        cache_d = []
#        cnt = Counter()
        for k_item, item_old in enumerate(items + [None]):
            # when k_item == L, item_old is None
            # complete new keys
            item_new = [get_unique_name('', d.keys(i)) for i in range(N)]
            is_new = k_item == L
            item_choices = [item_new] if is_new else [item_old, item_new]

            # d[index1:key, index2] == val
            index2_list = [] # variable index2 args

            # index2: single value
            for k in range(N):
                index2_list.append(k)

            # index2: multi values
            index2_list.append(list(range(N)))
            index2_list.append(_s[:])

            index2_list.append(list(range(N))*2)  # any duplicate names

            # d[index1:key, index2_1, index2_2, ...]
            index2_list.append(tuple(range(N)))

            index2_list.append(_s[::2])
            index2_list.append(list(range(0, N, 2)))
            index2_list.append(_s[:N+10])

            index2_list.append(_s[1:])
            index2_list.append(_s[:1])
            index2_list.append(_s[0:-1])

            index2_list.append([])
            index2_list.append(_s[0:0])


            index2_val_comb = [] # variable index2 args and resulting val
            for index2 in index2_list:
                for item in item_choices:
                    val = [index2, item] # value will be calucated later using index2

                    if isinstance(index2, int):
                        index2_val_comb.append([index2, val])
                        index2_val_comb.append([-N+index2, val])
                        index2_val_comb.append([names[index2], val])

                    elif isinstance(index2, list):
                        mixed_name = [names[index2[k]] if k%2 else index2[k] for k in range(len(index2))]
                        all_name = mget_list(names, index2)
                        all_neg = [-N+i if i >=0 else i for i in index2]
                        for arr in (index2, mixed_name, all_name, all_neg):
                            index2_val_comb.append([arr, val])
                            index2_val_comb.append([tuple(arr), val])

                    elif isinstance(index2, tuple):
                        mixed_name = [names[index2[k]] if k%2 else index2[k] for k in range(len(index2))]
                        all_name = mget_list(names, index2)
                        all_neg = [-N+i if i >=0 else i for i in index2]
                        for arr in (list(index2), mixed_name, all_name, all_neg):
                            index2_val_comb.append(arr + [val])

                    elif isinstance(index2, slice):
                        start_top_arr = [[], []]
                        for k, arr in zip([index2.start, index2.stop], start_top_arr):
                            arr.append(k)
                            if isinstance(k, int) and -N <= k < N:
                                arr.append(names[k])
                        step = index2.step
                        for start in start_top_arr[0]:
                            for stop in start_top_arr[1]:
                                index2_val_comb.append([_s[start : stop : step], val])

            keys = item_new if is_new else item_old
            for i, (index1, key) in enumerate(zip(names, keys)):
                # all possible syntax for [index1:key] part
                args = []
                args.append(_s[index1: key])
                args.append(_s[i: key])
                args.append(_s[-N+i: key])
                if i == 0:
                    args.append(key)
                if i == N-1:
                    args.append(_s[:key])

                index2_val_all= list(index2_val_comb) # copy

                index2_default = [k for k in range(N) if k != i]
                if len(index2_default) == 1:
                    index2_default = index2_default[0]

                for item in item_choices:
                    # no index2, d[index1:key] = value
                    val = [index2_default, item]
                    index2_val_all.append([val])

                for arg in args:
                    for row in index2_val_all:
                        val_index, item = row[-1]
                        if is_new:
                            # new item needs complete indices
                            all_indices = [i]
                            if isinstance(val_index, int):
                                all_indices.append(val_index)
                            elif isinstance(val_index, (tuple, list)):
                                all_indices.extend(val_index)
                            elif isinstance(val_index, slice):
                                all_indices.extend(list(range(N))[val_index])
                            if set(all_indices) != set(range(N)):
                                continue

                        value = mget_list(item, val_index)

                        if item == item_old: # no changes
                            d_new = d
                        else:
                            sign = [k_item, val_index, item]
                            try:
                                idx = cache_sign.index(sign)
                                d_new = cache_d[idx]
                            except ValueError:
                                items_new = list(items)
                                if is_new:
                                    items_new.append(item_new)
                                else:
                                    item_modified = list(item_old)
                                    mset_list(item_modified, val_index, value)
                                    items_new[k_item] = item_modified
                                d_new = MIDict(items_new, names)

                                cache_sign.insert(0, sign)
                                cache_d.insert(0, d_new)

                        index2 = row[:-1] # maybe 0, 1 or more
                        paras = []
                        if len(index2) == 0:
                            paras.append(arg)
                            # add a comma after arg only when arg is a slice
                            if isinstance(arg, slice):
                                paras.append((arg,))
                        else:
                            paras.append(tuple([arg] + index2))

                        for para in paras:
                            d2 = MIDict(items, names) # copy
#                            cnt[k_item] += 1

                            if not isinstance(arg, slice) and len(row) > 1:
                                # d[key, name], d[key, i], d[key, tuple] or d[key, k1, k2...] not working
                                if (len(para) == 2 and not isinstance(para[1], (list, slice))) or len(para) > 2:
                                    with self.assertRaises(KeyError):
                                        d2[para]
#                                        try:
#                                            d2[para]
#                                            print('not raise', para, value)
#                                        except:
#                                            raise
                                    continue

                            d2[para] = value
#                            try:
#                                d2[para] = value
#                            except:
#                                print('error', para, value)
#                                raise
                            self.assertEqual(d2, d_new,
                                '%r :not equal: %r, d[%r] = %r' % (d_new, d2, para, value))
#        print cnt

    def test_setitem_empty(self):
        d, items, names = self.get_data()
        N = len(names)

        item = items[0]
        idx1 = 1 if N == 2 else _s[1:]
        idx0 = 0 if N == 2 else _s[:-1]

        index1 = names[0] # main keys
        key = item[0 ]
        index2 = names[idx1]
        value = item[idx1]

        paras_names = []
        paras_names.append([_s[index1:key, index2], value, names])
        if N > 2:
            paras_names.append([(_s[index1:key],) + tuple(index2), value, names])
            paras_names.append([(_s[index1:key],) + tuple(index2), iter(value), names])

        default_names = ['index_%s'%(i+1) for i in range(N)]
        paras_names.append([_s[item[0], names[1:]], item[1:], default_names[:1]+names[1:]])
        paras_names.append([_s[:item[-1], names[:-1]], item[:-1], names[:-1]+default_names[-1:]])

        if N == 2:
            paras_names.append([key, value, default_names])
            paras_names.append([_s[:item[-1]], item[idx0], default_names])
            # name conflict
            default_names2 = ['index_2', get_unique_name('index_2', ['index_2'])]
            paras_names.append([_s['index_2':key], value, default_names2])

        for para, val, indices in paras_names:
            d = MIDict([item], indices) # with only one item
            d2 = MIDict() # empty dict
            d2[para] = val
            self.assertEqual(d2, d, '%r :not equal: %r, d[%r] = %r' % (d, d2, para, val))


    def test_setitem_error(self):
        d, items, names = self.get_data()
        N = len(names)
        M1 = N + 10 # out of range
        M2 = -N - 10

        index_exist = names[0]
        index_not_exist = get_unique_name('', names)

        assert len(items) > 1
        item = items[0]
        item2 = items[-1] # differ from item

        key_exist = item[0]
        key_not_exist = get_unique_name('', d)
        idx = 1 if N == 2 else _s[1:]
        value = item[idx]
        value2 = item2[idx]

        # d[index_exist:key_exist] is valid
        d[index_exist:key_exist]

        paras = []
        # index1 not exist
        for index1 in [index_not_exist, M1, M2]:
            for key in [key_exist, key_not_exist]:
                paras.append([_s[index1:key], value, KeyError])


        # index2 not exist; faked matched values
        arg_exist = _s[index_exist: key_exist]
        for index2 in [index_not_exist, M1, M2]:
            paras.append([(arg_exist, index2), 0, KeyError])
            for index2_exist in [index_exist, 0]:
                paras.append([(arg_exist, [index2, index2_exist]), [0,1], KeyError])
                paras.append([(arg_exist, index2, index2_exist), [0,1], KeyError])
                # extra arg after index2
                paras.append([(arg_exist, [index2, index2_exist], index2), [0,1], KeyError])

         # value exists
        paras.append([(arg_exist,-1), force_list(d.keys(-1))[-1], ValueExistsError]) # duplicate last index last value
        paras.append([arg_exist, value2, ValueExistsError])
        paras.append([_s[arg_exist, :], item2, ValueExistsError])
        paras.append([_s[index_exist: key_not_exist, :], item, ValueExistsError])

        for index1 in [index_exist, 0]:
            # index2 mot match value
            paras.append([_s[index1: key_exist, [0]], [], ValueError])
            # Indices of the new item do not match existing indices
            paras.append([_s[index1: key_not_exist, index1], key_not_exist, ValueError])



        for para, val, err in paras:
            with self.assertRaises(err):
                d[para] = val

        # empty dict
        d = MIDict()
        paras = []
        # int or slice not alllowed as index
        paras.append([_s[0:0, [key_exist]], [0]])
        paras.append([_s[0:0, 1:], [0]])
        paras.append([_s[index_exist: key_exist, 0], 0])
        paras.append([_s[index_exist: key_exist, 1:], [0]])
        paras.append([_s[key_exist, [1]], [0]])
        paras.append([_s[key_exist, 1:], [0]])

        for para, val in paras:
            with self.assertRaises(TypeError):
                d[para] = val

        paras = []
        paras.append([_s[index_exist: key_exist, [index_not_exist]], [0,1]]) # len not match
        for para, val in paras:
            with self.assertRaises(ValueError):
                d[para] = val

    def test_delitem(self):
        d, items, names = self.get_data()
        N = len(names)
        L = len(items)
        for k_item, item in enumerate(items):
            items_new = [items[k] for k in range(L) if k!= k_item]
            d_new = MIDict(items_new, names)
            for i, (index1, key) in enumerate(zip(names, item)):
                # all possible syntax for [index1:key] part
                args = []
                args.append(_s[index1: key])
                args.append(_s[i: key])
                args.append(_s[-N+i: key])
                if i == 0:
                    args.append(key)
                if i == N-1:
                    args.append(_s[:key])

                for arg in args:
                    d2 = d.copy()
                    del d2[arg]
                    self.assertEqual(d2, d_new)

    def test_delitem_error(self):
        d, items, names = self.get_data()
        d0 = MIDict()

        N = len(names)
        M1 = N + 10 # out of range
        M2 = -N - 10

        index_exist = names[0]
        index_not_exist = get_unique_name('', names)
        key_exist = list(d.keys())[0]
        key_not_exist = get_unique_name('', d)

        # d[index_exist:key_exist] is valid
        d[index_exist:key_exist]

        paras = []
        for index1 in [index_not_exist, M1, M2]: # index not exist
            for key in [key_exist, key_not_exist]:
                paras.append(_s[index1:key])

        for index1 in [index_exist, 0]:
            paras.append(_s[index1: key_not_exist]) # only key not exist

        for para in paras:
            for dct in [d, d0]:
                with self.assertRaises(KeyError):
                    del dct[para]

        # add index2
        paras = []
        paras.append(_s[index_exist:key_exist, []])
        paras.append(_s[index_exist:key_exist, :])
        paras.append(_s[index_exist:key_exist, 0])

        for para in paras:
            with self.assertRaises(TypeError): # unhashable type
                del d[para]


    def test_cmp(self):
        d, items, names = self.get_data()
        d2 = MIDict(d)
        dn = MIDict(items, map(str, range(len(names)))) # smaller names

        items2 = [[k+i for i in range(len(items[0]))] for k in range(len(items))]
        ds = MIDict(items2, names) # small values

        dct = dict(zip(range(5),range(5)))

        self.assertEqual(d, d2)

        for x in [1, dn, ds, dct]:
            self.assertNotEqual(d, x)
        if PY2:
            self.assertLess(d, dct)
            self.assertGreater(dct, d)
            for x in [1, dn, ds]:
                self.assertGreater(d, x)
                self.assertGreaterEqual(d, x)
                self.assertLess(x, d)
                self.assertLessEqual(x, d)
        else:
            for x in [dn, ds]:
                for m in ['__lt__',  '__gt__', '__le__','__ge__']:
                    with self.assertRaises(TypeError):
                        call(d, m, x)

    def test_repr(self):
        for cls in [MIMapping, MIDict, FrozenMIDict]:
            d0 = cls()
            d1, items, names = self.get_data(cls)
            for d in [d0, d1]:
                r = repr(d)
                d2 = eval(r)
                self.assertEqual(d.__class__, d2.__class__)
                self.assertEqual(d, d2)
                if d2.indices: # not empty
                    self.assertIs(d2.indices[0], d2)

    def test_reduce(self):
        for cls in [MIMapping, MIDict, FrozenMIDict]:
            d, items, names = self.get_data(cls)
            s = pickle.dumps(d)
            d2 = pickle.loads(s)
            self.assertEqual(d.__class__, d2.__class__)
            self.assertEqual(d, d2)
            self.assertIs(d2.indices[0], d2)


    def test_copy(self):
        d, items, names = self.get_data()
        for d2 in [d.copy(), MIDict(d)]:
            self.assertEqual(d.__class__, d2.__class__)
            self.assertEqual(d, d2)
            self.assertIs(d2.indices[0], d2)

    def test_reversed(self):
        d, items, names = self.get_data()

        self.assertEqual(list(reversed(d)), list(d.keys())[::-1])

        for index in names:
            keys = force_list(d.keys(index))
            rev = list(d.__reversed__(index))
            self.assertEqual(rev, keys[::-1])

        d = MIMapping() # empty
        self.assertEqual(list(reversed(d)), list(d.keys())[::-1])
        with self.assertRaises(KeyError):
            list(d.__reversed__(0))

    def test_keys_values_items(self):
        d, items, names = self.get_data()
        N = len(names)

        items = [tuple(it) for it in items]
        item_exist = items[0]
        item_not_exist = tuple(get_unique_name('', d.values(i)) for i in names)

        keys = [it[0] for it in items]
        key_exist = keys[0]
        key_not_exist = get_unique_name('', keys)

        if N == 2:
            values = [it[1] for it in items]
            value_not_exist = get_unique_name('', values)
        else:
            values = [tuple(it[1:]) for it in items]
            value_not_exist = tuple(get_unique_name('', d.values(i)) for i in names[1:])
        value_exist = values[0]

        funcs = ['keys', 'values', 'items']
        funcs_views = ['viewkeys', 'viewvalues', 'viewitems']
        gt_data = [keys, values, items]
        test_data = [[key_exist, key_not_exist], [value_exist, value_not_exist],
                     [item_exist, item_not_exist]]
        # check gt
        for f, fv, gt, test in zip(funcs, funcs_views, gt_data, test_data):
            if PY2:
                self.assertEqual(call(d, f), gt)
                self.assertEqual(list(call(d, fv)), gt)
            else:
                self.assertEqual(list(call(d, f)), gt)

            v_exist, v_not_exist = test
            if PY2:
                for fn in [f, fv]:
                    self.assertIn(v_exist, call(d, fn))
                    self.assertNotIn(v_not_exist, call(d, fn))
            else:
                self.assertIn(v_exist, call(d, f))
                self.assertNotIn(v_not_exist, call(d, f))

        # use index
        if PY2:
            funcs_all = funcs + funcs_views
        else:
            funcs_all = funcs

        for k in range(N):
            gt = [it[k] for it in items]
            for i in [k, names[k]]:
                for f in funcs_all:
                    self.assertEqual(list(call(d, f, i)), gt)

        index_not_exist = get_unique_name('', names)
        for i in [index_not_exist, N + 10, -N - 10]:
            for f in funcs_all:
                with self.assertRaises(KeyError):
                    list(call(d, f, i))

        # empty
        d = MIDict()
        gt_data = [[], [], []]
        for f, fv, gt in zip(funcs, funcs_views, gt_data):
            if PY2:
                self.assertEqual(call(d, f), gt)
                self.assertEqual(list(call(d, fv)), gt)
            else:
                self.assertEqual(list(call(d, f)), gt)

            v_not_exist = None
            if PY2:
                for fn in [f, fv]:
                    self.assertNotIn(v_not_exist, call(d, fn))
            else:
                self.assertNotIn(v_not_exist, call(d, f))

        for i in [index_not_exist, N + 10, -N - 10]:
            for f in funcs_all:
                with self.assertRaises(KeyError):
                    list(call(d, f, i))


    def test_viewdict(self):
        d, items0, names = self.get_data()
        idx = [[None, None], [0, -1], [-1, 0], [0, 1], [1, 0], [0, 0], [1, 1]]
        for i_key, i_value in idx:
            v = d.viewdict(i_key, i_value)
            if i_key is None:
                i_key = 0
            if i_value is None:
                i_value = -1
            keys = [it[i_key] for it in items0]
            values = [it[i_value] for it in items0]
            items = list(zip(keys, values))
            key_exist = keys[0]
            key_not_exist = get_unique_name('', keys)

            self.assertEqual(v.keys(), keys)
            self.assertEqual(list(v), keys)
            self.assertEqual(v.values(), values)
            self.assertEqual(v.items(), items)
            self.assertIn(key_exist, v)
            self.assertNotIn(key_not_exist, v)

        r = repr(v)
        v2 = eval(r)
        self.assertEqual(v2.index_key, v.index_key)
        self.assertEqual(v2.index_value, v.index_value)
        self.assertEqual(v2._mapping, v._mapping)

        with self.assertRaises(KeyError):
            d.viewdict(len(names) + 10)

        v = d.viewdict(0, -1)
        d.clear(True) # delete indices after view
        with self.assertRaises(KeyError):
            v.values() # index not found

        d = MIDict()
        v = d.viewdict()
        self.assertEqual(v.keys(), [])
        self.assertEqual(list(v), [])
        self.assertEqual(v.values(), [])
        self.assertEqual(v.items(), [])
        self.assertNotIn(None, v)

        with self.assertRaises(KeyError):
            d.viewdict(0, 1)

    def test_clear(self):
        d0, items, names = self.get_data()
        d = d0.copy()
        d.clear() # index names still exist
        self.assertEqual(d, MIDict([], names))

        d = d0.copy()
        d.clear(clear_indices=True)
        self.assertEqual(d, MIDict())

    def test_update(self):
        d, items, names = self.get_data()
        N = len(names)
        L = len(items)
        for k in range(L+1):
            d2 = MIDict(items[:k], names)
            d2.update(items[k:])
            self.assertEqual(d2, d)

        # assign index names too
        d2 = MIDict()
        d2.update(d)
        self.assertEqual(d2, d)

        d2 = MIDict()
        d2.update(items, names)
        self.assertEqual(d2, d)

        with self.assertRaises(ValueError):
            d.update(items, names) # no names allowed

        with self.assertRaises(ValueError):
            items2 = [list(range(N+1))] # len not equal
            d.update(items2)

    def test_rename_index(self):
        d, items, names = self.get_data()
        N = len(names)
        names2 = map(str, range(N))

        d2 = d.copy()
        d2.rename_index(names2)
        self.assertEqual(list(d2.indices.keys()), names2)

        paras = []
        for k in range(N):
            paras.append([k, k])
            paras.append([names[k], k])

        for k in range(N+1):
            paras.append([_s[:k], _s[:k]])
            paras.append([names[:k], _s[:k]])

        for i_old, idx in paras:
            i_new = names2[idx]
            names_new = list(names)
            mset_list(names_new, idx, mget_list(names2, idx))
            d2 = d.copy()
            d2.rename_index(i_old, i_new)
            self.assertEqual(list(d2.indices.keys()), names_new)

        with self.assertRaises(ValueError):
            d.rename_index(names[:0], names2) # len not equal

        with self.assertRaises(ValueError):
            d.rename_index(map(str, range(N+10))) # len not equal

        with self.assertRaises(ValueError):
            d.rename_index([''] * N) # duplicate names


    def test_reorder_indices(self):
        d, items, names = self.get_data()
        N = len(names)

        a = list(range(N))
        paras = []
        paras.append(a) # different orders
        paras.append(a[::-1])
        paras.append(a[::2] + a[1::2])
        paras.append(a[N//2:] + a[:N//2])
        for idx in paras:
            names2 = mget_list(names, idx)
            for order in [idx, names2]:
                d2 = d.copy()
                d2.reorder_indices(order)
                self.assertEqual(list(d2.indices.keys()), names2)

        with self.assertRaises(KeyError):
            d.reorder_indices([]) # len not equal

        d2 = MIDict()
        d2.reorder_indices([])
        self.assertEqual(list(d2.indices.keys()), [])

    def test_add_index(self):
        d, items, names = self.get_data()
        N = len(names)
        L = len(items)

        d0 = MIDict()
        for k in range(N):
            values = [it[k] for it in items]
            d0.add_index(values, names[k])
        self.assertEqual(d0, d)

        d2 = MIDict(items) # default index names
        d0 = MIDict()
        for k in range(N):
            values = [it[k] for it in items]
            d0.add_index(values)
        self.assertEqual(d0, d2)

        with self.assertRaises(ValueError):
            d.add_index([0] * L) # duplicate values

        with self.assertRaises(ValueError):
            d.add_index(list(range(L + 10))) # len not equal

        with self.assertRaises(ValueError):
            d.add_index(list(range(L)), names[0]) # duplicate index name


    def test_remove_index(self):
        d, items, names = self.get_data()
        N = len(names)
        d0 = MIDict()

        d2 = d.copy()
        for index in names:
            d2.remove_index(index)
        self.assertEqual(d2, d0)

        d2 = d.copy()
        for index in range(N-1, -1, -1):
            d2.remove_index(index)
        self.assertEqual(d2, d0)

        d2 = d.copy()
        d2.remove_index(names)
        self.assertEqual(d2, d0)

        d2 = d.copy()
        d2.remove_index(list(range(N)))
        self.assertEqual(d2, d0)


class TestMIDict_2_Indices(TestMIDict_3_Indices):

    def get_data(self, cls=MIDict):
        items = [['jack', 1],
#                 ['tony', 2],
                 ['alice', 3]]
        names = ['name', 'uid']
        d =  cls(items, names)
        return d, items, names

    def test_convert_dict(self):
        d1, items, names = self.get_data()
        d0 = MIDict()
        for d in [d1, d0]:
            for cls in [dict, OrderedDict]:
                normal_d = cls(d.items())
                for d_var in [d, cls(d), d.todict(cls)]:
                    self.assertEqual(d_var, normal_d)
                    self.assertEqual(normal_d, d_var)



    def test_compatible_dict(self):
        d, items, names = self.get_data()
        dct = dict(items)
        od = OrderedDict(items)

        key_exist = force_list(d.keys())[0]
        key_not_exist = get_unique_name('', d)
        value_exist = force_list(d.values())[0]
        value_not_exist = get_unique_name('', d.values())
        item_exist = force_list(d.items())[0]
        item_not_exist = (key_not_exist, value_not_exist)

        funcs = ['__len__', ]
        for d2 in [dct, od]:
            for f in funcs:
                self.assertEqual(call(d, f), call(d2, f))

        if PY2:
            funcs_ordered = ['keys', 'values', 'items']
            for f in funcs_ordered:
                self.assertEqual(set(call(d, f)), set(call(dct, f)))
                self.assertEqual(call(d, f), call(od, f))

        funcs_ordered_views = ['viewkeys', 'viewvalues', 'viewitems']
        if PY3:
            funcs_ordered_views = ['keys', 'values', 'items']
        test_data = [[key_exist, key_not_exist], [value_exist, value_not_exist],
                     [item_exist, item_not_exist]]
        for f, data in zip(funcs_ordered_views, test_data):
            self.assertEqual(set(call(d, f)), set(call(dct, f)))
            self.assertEqual(list(call(d, f)), list(call(od, f)))
            for x in data:
                self.assertEqual(x in call(d, f), x in call(dct, f))
                self.assertEqual(x in call(d, f), x in call(od, f))



        funcs_key = ['__contains__', 'get']
        if PY2:
            funcs_key.append('has_key')
        for d2 in [dct, od]:
            for f in funcs_key:
                for key in [key_exist, key_not_exist]:
                    self.assertIs(call(d, f, (key,)), call(d2, f, (key,)))

        # same Key Error
        exc_types = []
        for d2 in [d, dct, od]:
            try:
                d[key_not_exist]
            except Exception as e:
                exc_types.append(type(e))
        for t in exc_types[1:]:
            self.assertEqual(exc_types[0], t)




if __name__ == '__main__':
    ''
    unittest.main(verbosity=2)