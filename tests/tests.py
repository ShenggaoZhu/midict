# -*- coding: utf-8 -*-
"""
Created on Wed Apr 20 11:13:35 2016

@author: Shenggao
"""
#from __future__ import absolute_import
import unittest
from midict import *


class TestMIDict_3(unittest.TestCase):

    def getData(self):
        item1 = ['jack', 1, '192.1']
        item2 = ['tony', 2, '192.2']
        names = ['name', 'uid', 'ip']
        d =  MIDict([item1, item2], names)
        return d, names, item1, item2

    def test_getitem(self):
        d, names, item1, item2 = self.getData()
        N = len(names)
        for item in [item1, item2]:
            for i, (index1, key) in enumerate(zip(names, item)):
                # all possible syntax for [index1:key]
                args = []
                args.append(slice(index1,key))
                args.append(slice(i,key))
                args.append(slice(-N+i,key))
                if i == 0:
                    args.append(key)
                if i == N-1:
                    args.append(slice(None, key))

                # d[index1:key] == value
                value = [v for v in item if v != key]
                if len(value) == 1:
                    value = value[0]

                for arg in args:
                    self.assertEqual(d[arg], value,
                        '%r :not equal: d[%r] = %r' % (value, arg, d[arg]))
                    if isinstance(arg, slice):
                        # add a comma after arg
                        self.assertEqual(d[arg,], value,
                            '%r :not equal: d[%r] = %r' % (value, arg, d[arg]))

                # d[index1:key, index2] == val
                index2_val = [] # index2 args and resulting val
                index2_val.append([tuple(names), item])
                index2_val.append([list(names), item])
                index2_val.append([tuple(range(N)), item])
                index2_val.append([list(range(N)), item])
                index2_val.append([slice(None, None, None), item])

                index2_val.append([list(names)*2, item*2]) # any duplicate names
                index2_val.append([list(range(N))*2, item*2])

                # d[index1:key, index2_1, index2_2, ...]
                index2_val.append(list(names) + [item])
                index2_val.append(list(range(N)) + [item])

                index2_val.append([slice(None, None, 2), item[::2]])
                index2_val.append([slice(1, None), item[1:]])
                index2_val.append([slice(None, 1), item[:1]])
                index2_val.append([slice(0, -1), item[0:-1]])
                index2_val.append([slice(names[1], None), item[1:]])
                index2_val.append([slice(None, names[1]), item[:1]])
                index2_val.append([slice(names[0], names[-1]), item[0:-1]])

                index2_val.append([(), []])
                index2_val.append([[], []])
                index2_val.append([slice(0, 0), []])

                for arg in args:
                    for row in index2_val:
                        val = row[-1]
                        para = tuple([arg] + row[:-1]) # [index1:key, index2]
                        index2 = row[:-1] # maybe 1 or more
                        if len(index2) == 1:
                            index2 = index2[0]

                        if not isinstance(arg, slice):
                            # d[key, tuple] or d[key, k1, k2...] not working
                            if isinstance(index2, tuple) or len(para) > 2:
                                with self.assertRaises(KeyError):
                                    d[para]
                                continue

                        self.assertEqual(d[para], val,
                            '%r :not equal: d[%r] = %r' % (val, para, d[para]))



#    def test_setitem(self):
#        d = self.d
#        d['jack'] = 10
#        d['alice'] = 2 # -> ValueError
#        d['jack'] = 2 # -> ValueError
#        d[:2] = 'jack'
#        d['name':'jack', :] = ['tony', 22]


class TestMIDict_2(TestMIDict_3):

    def getData(self):
        item1 = ['jack', 1]
        item2 = ['tony', 2]
        names = ['name', 'uid']
        d =  MIDict([item1, item2], names)
        return d, names, item1, item2

    def test_compat_dict(self):
        from collections import OrderedDict
        d, names, item1, item2 = self.getData()
        for cls in [dict, OrderedDict]:
            normal_d = cls([item1, item2])
            for d_var in [d, cls(d), d.todict(cls)]:
                self.assertEqual(d_var, normal_d)
                self.assertEqual(normal_d, d_var)




if __name__ == '__main__':
    ''
    unittest.main(verbosity=2)