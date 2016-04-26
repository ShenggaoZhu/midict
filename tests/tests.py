# -*- coding: utf-8 -*-
"""
Created on Wed Apr 20 11:13:35 2016

@author: Shenggao
"""
#from __future__ import absolute_import
import unittest
from collections import OrderedDict, Counter
from midict.midict import *

def call(obj, func_name, *args, **kw):
    'call function by `func_name` of obj'
    func = getattr(obj, func_name)
    return func(*args, **kw)


class EasyGetItem(object):
    '''
    Easily obtain the argument (e.g., slice) of __getitem__() via the bracket syntax.

    _s = EasyGetItem()
    _s[1:] -> slice(1, None, None)
    _s['a':1,'b'] -> (slice('a', 1, None), 'b')
    '''
    def __getitem__(self, arg):
        return arg


_s = EasyGetItem()





#==============================================================================
# test cases
#==============================================================================




class TestMIDict_Basic(unittest.TestCase):

    def test_construction(self):
        data = []
        N_items = 3
        for k_indices in [2, 3, 5, 10]: # number of indices
            items = []
            for n in range(N_items):
                item = [i+n for i in range(k_indices)] # populate values
                items.append(item)
            names = map(str, range(k_indices))
            data.append([items, names])
        for items, names in data:
            d = MIDict(items, names)
            self.assertEqual(d.indices.keys(), names)
            self.assertEqual(d.items(), [tuple(it) for it in items])

    def test_construction_error(self):
        ''


class TestMIDict_3(unittest.TestCase):

    def get_data(self):
        items = [['jack', 1, (192,1)],
#                 ['tony', 2, (192,2)],
                 ['alice', 3, (192,3)]]
        names = ['name', 'uid', 'ip']
        d =  MIDict(items, names)
        return d, names, items

    def test_getitem(self):
        d, names, items = self.get_data()
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
                        if -N <= k < N:
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
        d, names, items = self.get_data()
        N = len(names)
        M1 = N + 10 # out of range
        M2 = -N - 10

        index_exist = names[0]
        index_not_exist = get_unique_name('', names)
        key_exist = d.keys()[0]
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
                paras.append((arg_exist, [index2, index2_exist], index2))


        for para in paras:
            with self.assertRaises(KeyError):
                d[para]



    def test_setitem_nonempty(self):
        # modify existing items, construct a new MIDict, and compare with results of setitem
        d, names, items = self.get_data()
        N = len(names)
        L = len(items)

        # cached signature and d_new
        cache_sign = []
        cache_d = []
        cnt = Counter()
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
                            if -N <= k < N:
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
                            cnt[k_item] += 1

                            if not isinstance(arg, slice) and len(row) > 1:
                                # d[key, name], d[key, i], d[key, tuple] or d[key, k1, k2...] not working
                                if (len(para) == 2 and not isinstance(para[1], (list, slice))) or len(para) > 2:
                                    with self.assertRaises(KeyError):
                                        try:
                                            d2[para]
                                            print 'not raise', para, value
                                        except:
                                            raise
                                    continue

                            try:
                                d2[para] = value
                            except:
                                print 'error', para, value
                                raise
                            self.assertEqual(d2, d_new,
                                '%r :not equal: %r, d[%r] = %r' % (d_new, d2, para, value))
        print cnt

    def test_setitem_empty(self):
        d, names, items = self.get_data()
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
        d, names, items = self.get_data()
        N = len(names)
        M1 = N + 10 # out of range
        M2 = -N - 10

        index_exist = names[0]
        index_not_exist = get_unique_name('', names)

        item = items[0]
        key_exist = item[0]
        key_not_exist = get_unique_name('', d)
        idx = 1 if N == 2 else _s[1:]
        value = item[idx]

        # d[index_exist:key_exist] is valid
        d[index_exist:key_exist]

        paras = []
        for index1 in [index_not_exist, M1, M2]: # index1 not exist
            for key in [key_exist, key_not_exist]:
                paras.append([_s[index1:key], value, KeyError])

        for index1 in [index_exist, 0]:
            # index2 mot match value
            paras.append([_s[index1: key_exist, [0]], [], ValueError])
            # Indices of the new item do not match existing indices
            paras.append([_s[index1: key_not_exist, index1], key_not_exist, ValueError])

        # index2 not exist; faked matched values
        arg_exist = _s[index_exist: key_exist]
        for index2 in [index_not_exist, M1, M2]:
            paras.append([(arg_exist, index2), 0, KeyError])
            for index2_exist in [index_exist, 0]:
                paras.append([(arg_exist, [index2, index2_exist]), [0,1], KeyError])
                paras.append([(arg_exist, index2, index2_exist), [0,1], KeyError])
                # extra arg after index2
                paras.append([(arg_exist, [index2, index2_exist], index2), [0,1], KeyError])

        for para, val, err in paras:
            with self.assertRaises(err):
                d[para] = val

        # empty dict
        d = MIDict()
        paras = []
        # int or slice not alllowed as index
        paras.append([(arg_exist, 0), 0])
        paras.append([(arg_exist, _s[1:]), [0]])
        paras.append([(_s[0, key_exist], _s[1:]), [0]])

        for para, val in paras:
            with self.assertRaises(TypeError):
                d[para] = val


class TestMIDict_2(TestMIDict_3):

    def get_data(self):
        items = [['jack', 1],
#                 ['tony', 2],
                 ['alice', 3]]
        names = ['name', 'uid']
        d =  MIDict(items, names)
        return d, names, items

    def test_convert_dict(self):
        d, names, items = self.get_data()
        for cls in [dict, OrderedDict]:
            normal_d = cls(items)
            for d_var in [d, cls(d), d.todict(cls)]:
                self.assertEqual(d_var, normal_d)
                self.assertEqual(normal_d, d_var)

    def test_compatible_dict(self):
        d, names, items = self.get_data()
        dct = dict(items)
        od = OrderedDict(items)

        key_exist = d.keys()[0]
        key_not_exist = get_unique_name('', d)

        funcs = ['__len__', ]
        for d2 in [dct, od]:
            for f in funcs:
                self.assertEqual(call(d, f), call(d2, f))

        funcs_ordered = ['keys', 'values', 'items']
        for f in funcs_ordered:
            self.assertItemsEqual(call(d, f), call(dct, f))
            self.assertEqual(call(d, f), call(od, f))

        funcs_ordered_views = ['viewkeys', 'viewvalues', 'viewitems']
        for f in funcs_ordered_views:
            self.assertItemsEqual(list(call(d, f)), list(call(dct, f)))
            self.assertEqual(list(call(d, f)), list(call(od, f)))

        funcs_key = ['__contains__', 'has_key', 'get']
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