# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 22:46:14 2016

@author: shenggao
"""

from collections import (Hashable, ItemsView, KeysView, Mapping, OrderedDict, ValuesView,
                         _get_ident)
from types import NoneType


def od_replace_key(od, key, new_key, *args, **kw):
    '''
    Replace key(s) in OrderedDict ``od`` by new key(s) in-place (i.e.,
    preserving the order(s) of the key(s))

    Optional new value(s) for new key(s) can be provided as a positional
    argument (otherwise the old value(s) will be used):

        od_replace_key(od, key, new_key, new_value)

    To replace multiple keys, pass argument ``key`` as a list instance,
    or explicitly pass a keyword argument ``multi=True``:

        od_replace_key(od, keys, new_keys, [new_values,] multi=True)

    '''
    multi = kw.get('multi', False) or isinstance(key, list)

    if multi:
        if len(key) != len(new_key):
            raise ValueError('Length of keys (%s) does not match '
                             'length of new keys (%s)' % (len(key), len(new_key)))
        if args:
            new_value = args[0]
            if len(new_key) != len(new_value):
                raise ValueError('Length of new keys (%s) does not match '
                                 'length of new values (%s)' %
                                 (len(new_key), len(new_value)))
            for k_old, k_new, v_new in zip(key, new_key, new_value):
                od_replace_key(od, k_old, k_new, v_new)
        else:
            for k_old, k_new in zip(key, new_key):
                od_replace_key(od, k_old, k_new)
        return

    if new_key == key:
        return
    if new_key in od:
        del od[new_key]

    _map = od._OrderedDict__map
    link = _map[key]
    link[2] = new_key
    del _map[key]
    _map[new_key] = link
    value = dict.pop(od, key)
    if args:
        value = args[0]
    dict.__setitem__(od, new_key, value)


def od_reorder_keys(od, keys_in_new_order):
    '''
    Reorder the keys in an OrderedDict ``od`` in-place.
    '''
    if set(od.keys()) != set(keys_in_new_order):
        raise KeyError('Keys in the new order do not match existing keys')
    for key in keys_in_new_order:
        od[key] = od.pop(key)
    return od


class AttrDict(dict):
    '''
    A dictionary that can get/set/delete a key using the attribute syntax
    if it is a valid Python identifier. (``d.key`` <==> d['key'])

    Note that it treats an attribute as a dictionary key only when it can not
    find a normal attribute with that name. Thus, it is the programmer's
    responsibility to choose the correct syntax while writing the code.

    Be aware that besides all the inherited attributes, AttrDict has an
    additional internal attribute "_AttrDict__attr2item".

    Example::

        d = AttrDict(__init__='value for key "__init__"')
        d.__init__ -> <bound method AttrDict.__init__>
        d["__init__"] -> 'value for key "__init__"'
    '''

    def __init__(self, *args, **kw):
        '''
        set any attributes here (or in subclass) - before __init__()
        so that these remain as normal attributes
        '''
        super(AttrDict, self).__init__(*args, **kw)
        self.__attr2item = True  # transfered to _AttrDict__attr2item

    # easy access of items through attributes, e.g., d.key
    def __getattr__(self, item):
        """Maps values to attributes.
        Only called if there *isn't* an attribute with this name
        """
        # Note: hasattr() and dir(self) calls __getattr__() internally

        # Note: this allows normal attributes access in the __init__ method

        if '_AttrDict__attr2item' not in self.__dict__:  # slot??
            raise AttributeError(item)

        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError(item)

    def __setattr__(self, item, value):
        """Maps attributes to values.
        Only if initialized and there *isn't* an attribute with this name
        """
        # Note: this allows normal attributes access in the __init__ method

        super_setattr = super(AttrDict, self).__setattr__

        if '_AttrDict__attr2item' not in self.__dict__:  # slot??
            return super_setattr(item, value)

        if item in dir(self):  # any normal attributes are handled normally
            return super_setattr(item, value)

        return self.__setitem__(item, value)

    def __delattr__(self, item):
        """Maps attributes to values.
        Only if there *isn't* an attribute with this name
        """
        if item in dir(self):  # any normal attributes are handled normally
            super(AttrDict, self).__delattr__(item)
        else:
            self.__delitem__(item)


def _index_to_key(keys, index):
    'Convert int ``index`` to the corresponding key in ``keys``'
    if isinstance(index, int):
        try:
            return keys[index]
        except IndexError:
            # use KeyError rather than IndexError for compatibility
            #            IndexNotExistsError()
            raise KeyError('Index out of range of keys: %s' % (index,))
    return index


def _key_to_index(keys, key, single=False):
    'convert `key` to int or list of int'
    if isinstance(key, int): # validate the int index
        try:
            keys[key]
        except IndexError:
            raise KeyError('Index out range of keys: %s' % (key,))
        if key < 0:
            key += len(keys)
        return key
#    keys = d.keys()
    if not single:
        if isinstance(key, (tuple, list)):
            return [_key_to_index_single(keys, k) for k in key]

        if isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
            try:
                _check_index_name(start)
                start = keys.index(start)
            except TypeError:
                pass
            try:
                _check_index_name(stop)
                stop = keys.index(stop)
            except TypeError:
                pass
#            return slice(start, stop, step)
            args = slice(start, stop, step).indices(len(keys))
            return range(*args)
    try:
        return keys.index(key)
    except IndexError:
        raise KeyError('Key not found: %s' % (key,))


def _key_to_index_single(keys, key):
    return _key_to_index(keys, key, single=True)


def convert_index_keys(d, item):
    # use a separate function rather than a method inside the class IndexDict
    '''
    Convert ``item`` in various types to a single key or a list of keys.
    '''

    keys = d.keys()
    # use KeyError for compatibility of normal use

    # int item will be interpreted as the index rather than key!!
    if isinstance(item, int):
        item = _index_to_key(keys, item)
        single = True

    elif isinstance(item, (tuple, list)):
        item2 = []
        for i in item:
            i = _index_to_key(keys, i)
            item2.append(i)
        item = item2
        single = False

    elif isinstance(item, slice):
        start, stop, step = item.start, item.stop, item.step
        # None is not interpreted as a key
        if not isinstance(start, (NoneType, int)):
            try:
                start = keys.index(start)
            except ValueError:
                raise KeyError('%s is not in the list of keys' % (start,))
        if not isinstance(stop, (NoneType, int)):
            try:
                stop = keys.index(stop)
            except ValueError:
                raise KeyError('%s is not in the list of keys' % (stop,))
        item = keys[start:stop:step]
        single = False

    else:  # other types, treated as a single key
        single = True

    return item, single


def _check_IndexDict_key(key):
    'raise TypeError if ``key`` is int, tuple or NoneType'
    if isinstance(key, (int, tuple, NoneType)):
        raise TypeError('Key must not be int or tuple or None: %s' % (key,))


class IndexDict(dict):
    '''
    A dictionary that supports flexible indexing (get/set/delete) of
    multiple keys via an int, tuple, list or slice object.

    The type of a valid key in IndexDict should not be int, tuple, or NoneType.

    To index one or more items, use a proper ``item`` argument with the
    bracket syntax: ``d[item]``. The possible types and contents of ``item``
    as well as the corresponding values are summarized as follows:

    ============= ================================== ======================
        type        content of the ``item`` argument    corresponding values
    ============= ================================== ======================
    int           the index of a key in d.keys()     the value of the key
    tuple/list    multiple keys or indices of keys   list of values
    slice         "key_start : key_stop : step"      list of values
    other types   a normal key                       the value of the key
    ============= ================================== ======================

    The tuple/list syntax can mix keys with indices of keys.

    The slice syntax means a range of keys (like the normal list slicing),
    and the ``key_start`` and ``key_stop`` parameter can be a key, the index
    of a key, or None (which can be omitted).

    When setting items, the slice and int syntax (including int in the tuple/list
    syntax) can only be used to change values of existing keys, rather than
    set values for new keys.


    Examples:

    d = IndexDict(a=1,b=2,c=3)

    d -> {'a': 1, 'c': 3, 'b': 2}
    d.keys() -> ['a', 'c', 'b']

    d['a'] -> 1
    d[0] -> 1
    d['a','b'] <==> d[('a','b')] <==> d[['a','b']] -> [1, 2]
    d[:] -> [1,3,2]
    d['a':'b'] <==> d[0:2] <==> d['a':2] <==> d['a':-1] -> [1, 3]
    d[0::2] -> [1, 2]

    d[0] = 10 # d -> {'a': 10, 'c': 3, 'b': 2}
    d['a':-1] = [10, 30] # d -> {'a': 10, 'c': 30, 'b': 2}

    d[5] = 10 -> KeyError: 'Index out of range of keys: 5'
    '''

    def __init__(self, *args, **kw):
        'check key is valid'
        if args:
            for key, value in args[0]:
                _check_IndexDict_key(key)
        super(IndexDict, self).__init__(*args, **kw)

#

    def __getitem__(self, item):
        '''
        Get one or more items using flexible indexing.
        '''
        item2, single = convert_index_keys(self, item)
        super_getitem = super(IndexDict, self).__getitem__
        if single:
            return super_getitem(item2)
        else:
            return map(super_getitem, item2)

    def __setitem__(self, item, value):
        '''
        Set one or more items using flexible indexing.

        The slice and int syntax (including int in the tuple/list syntax) can
        only be used to change values of existing keys, rather than set values
        for new keys.
        '''
        item2, single = convert_index_keys(self, item)
        super_setitem = super(IndexDict, self).__setitem__
        if single:
            super_setitem(item2, value)
        else:
            if len(item2) != len(value):
                raise ValueError(
                    'Number of keys (%s) based on argument %s does not match '
                    'number of values (%s)' % (len(item2), item, len(value)))
            map(_check_IndexDict_key, item2)
            return map(super_setitem, item2, value)

    def __delitem__(self, item):
        '''
        Delete one or more items using flexible indexing.
        '''
        item2, single = convert_index_keys(self, item)
        super_delitem = super(IndexDict, self).__delitem__
        if single:
            return super_delitem(item2)
        else:
            return map(super_delitem, item2)

    def __contains__(self, item):
        'Check if the dictionary contains one or more items using flexible indexing.'
        try:
            self.__getitem__(item)
            return True
        except Exception:
            return False


class AttrOrdDict(AttrDict, OrderedDict):
    pass


class IdxOrdDict(IndexDict, AttrDict, OrderedDict):
    pass


def _check_index_name(name):
    'Check if index name is valid'
    if not isinstance(name, (str, unicode)):
        raise TypeError('Index name must be a str or unicode. '
                        'Found type %s for %s' % (type(name), name))


def _get_unique_name(name, collection):
    '''
    Generate a unique name by appending a sequence number to
    the original name so that it is not contained in the collection.
    ``collection`` has a __contains__ method (tuple, list, dict, etc.)
    '''
    if name not in collection:
        return name
    i = 1
    while True:
        i += 1
        name2 = '%s_%s' % (name, i)
        if name2 not in collection:
            return name2


def _get_value_len(value):
    'Get length of value. if value has no len(), convert it to list first'
    try:
        Nvalue = len(value)
    except TypeError:
        # convert iterator/generator to list
        value = list(value)
        Nvalue = len(value)
    return Nvalue, value


def mid_parse_args(self, args, ingore_index2=False, allow_new=False):
    '''
    Parse the arguments for indexing in MIDict.

    Full syntax: ``d[index1:key, index2]``.

    ``index2`` can be flexible indexing (int, list, slice etc.) as in ``IndexDict``.

    Short syntax:

    * d[key] <==> d[key,] <==> d[first_index:key, all_indice_except_first]
    * d[:key] <==> d[:key,] <==> d[None:key] <==> d[last_index:key, all_indice_except_last]
    * d[key, index2] <==> d[first_index:key, index2] # this is valid
      # only when index2 is a list or slice object
    * d[index1:key, index2_1, index2_2, ...] <==> d[index1:key, (index2_1, index2_2, ...)]

    '''
    empty = len(self.indices) == 0
    if empty and not allow_new:
        raise KeyError('Item not found (dictionary is empty): %s' % (args,))

    names = self.indices.keys()

    Nargs = len(args) if isinstance(args, tuple) else 1

    _default = object()
    index1 = index2 = _default

    if isinstance(args, tuple):
        # easy handle of default logic (use continue/break as shortcut)
        for _ in (1,):
            if ingore_index2:
                continue

            if isinstance(args[0], slice):
                index1, key = args[0].start, args[0].stop

                if Nargs == 2:
                    index2 = args[1]
                elif Nargs > 2:
                    index2 = args[1:]
                break

            if Nargs > 1 and isinstance(args[1], (list, slice)):
                key, index2 = args
                break
        else:
            key = args

    elif isinstance(args, slice):
        index1, key = args.start, args.stop

    else:
        key = args

    if empty:
        index1_last = False

        exist_names = []  # list of names already passed in as arguments
        if index1 is not _default:
            if index1 is None: # slice syntax d[:key]
                index1_last = True
                index1 = _default
            elif isinstance(index1, int):
                raise TypeError('Index1 can not be int when dictionary '
                                'is empty: %s' % (index1,))
            else:
                _check_index_name(index1)
                exist_names.append(index1)
        if index2 is not _default:
            if isinstance(index2, (tuple, list)):
                map(_check_index_name, index2)
                exist_names.extend(index2)
            elif isinstance(index2, (int, slice)):
                raise TypeError('Index2 can not be int or slice when '
                                'dictionary is empty: %s' % (index2,))
            else:
                _check_index_name(index2)
                exist_names.append(index2)

        # auto generate index names and avoid conficts with existing names
        if index1 is _default:
            if index1_last:
                if len(exist_names) > 1: # index2 is specified
                    name1 = 'index_%s' % (len(exist_names) + 1)
                else:
                    name1 = 'index_2'
            else:
                name1 = 'index_1'
            index1 = _get_unique_name(name1, exist_names)
            exist_names.append(index1)

        if index2 is _default:
            name2 = 'index_1' if index1_last else 'index_2'
            index2 = _get_unique_name(name2, exist_names)

        return index1, key, index2, index1_last

    # not empty:

    if index1 is _default:  # not specified
        index1 = 0
    elif index1 is None:  # slice syntax d[:key]
        index1 = -1

    # index1 is always returned as an int
    index1 = _key_to_index_single(names, index1)

    try:
        item = mid_get_item(self, key, index1)
    except KeyError:
        if allow_new:  # new key for setitem; item_d = None
            item = None
        else:
            raise KeyError('Key not found in index "%s": %s' % (index1, key))

    if ingore_index2:  # used by delitem
        return item

    if index2 is _default:  # not specified
        # index2 defaults to all indices except index1
        if len(names) == 1:
            index2 = 0  # index2 defaults to the only one index
        else:
            index2 = range(len(names))
            index2.remove(index1)
            if len(index2) == 1:  # single index
                index2 = index2[0]
    else:
        # index2 is always returned as int or list of int
        index2 = _key_to_index(names, index2)

    if item is None:  # allow_new
        return index1, key, index2, None, None

    try:
        value = mget_list(item, index2)
    except IndexError:
        raise KeyError('Index not found: %s' % (index2,))
    return index1, key, index2, item, value


def mget_list(item, index):
    'get mulitple items via index of int, slice or list'
    if isinstance(index, (int, slice)):
        return item[index]
    else:
        return map(item.__getitem__, index)


def mset_list(item, index, value):
    'set mulitple items via index of int, slice or list'
    if isinstance(index, (int, slice)):
        item[index] = value
    else:
        return map(item.__setitem__, index, value)


def mid_get_item(self, key, index=0):
    'return list of item'
    index = _key_to_index_single(self.indices.keys(), index)
    if index != 0:
        key = self.indices[index][key]  # always use first index key
    # key must exist
    value = super(MIMapping, self).__getitem__(key)
    N = len(self.indices)
    if N == 1:
        return [key]

    if N == 2:
        value = [value]
    return [key] + value


def _mid_setitem(self, args, value):
    'Separate __setitem__ function of MIMapping'
    indices = self.indices
    N = len(indices)
    empty = N == 0
    if empty:
        index1, key, index2, index1_last = mid_parse_args(self, args, allow_new=True)
        exist_names = [index1]
        item = [key]
        try:
            _check_index_name(index2)
            exist_names.append(index2)
            item.append(value)
        except TypeError:
            Nvalue, value = _get_value_len(value)
            if len(index2) != Nvalue:
                raise ValueError(
                    'Number of keys (%s) based on argument %s does not match '
                    'number of values (%s)' % (len(index2), index2, Nvalue))
            exist_names.extend(index2)
            item.extend(value)
        if index1_last:
            exist_names = exist_names[1:] + exist_names[:1]
            item = item[1:] + item[:1]

        _mid_init(self, [item], exist_names)
        return

    index1, key, index2, item, old_value = mid_parse_args(self, args, allow_new=True)
    names = indices.keys()
    is_new_key = item is None
    single = isinstance(index2, int)

    if single:
        index2_list = [index2]
        value = [value]
        old_value = [old_value]
    else:
        index2_list = index2
        Nvalue, value = _get_value_len(value)
        if len(index2_list) != Nvalue:
            raise ValueError('Number of keys (%s) based on argument %s does not match '
                             'number of values (%s)' % (len(index2_list), index2, Nvalue))
        if is_new_key:
            old_value = [None] * Nvalue  # fake it

    # remove duplicate in index2_list
    index2_d = OrderedDict()
    for e, index in enumerate(index2_list):
        index2_d[index] = e # order of each unique index
    if len(index2_d) < len(index2_list): # exist duplicate indices
        idx = index2_d.values()
        index2_list = mget_list(index2_list, idx)
        value = mget_list(value, idx)
        old_value = mget_list(old_value, idx)

    # check duplicate values
    for i, v, old_v in zip(index2_list, value, old_value):
        # index2_list may contain index1; not allow duplicate value for index1 either
        if v in indices[i]:
            if is_new_key or v != old_v:
                raise ValueExistsError(v, i)

    if is_new_key:  # new key
        if set(index2_list + [index1]) != set(range(N)):
            raise ValueError('Indices of the new item do not match existing indices')

        d = {}
        d[index1] = key
        # index2_list may also override index1
        d.update(zip(index2_list, value))
        values = [d[i] for i in range(N)]  # reorder based on the indices
        key = values[0]
        val = values[1] if len(values) == 2 else values[1:]
        super(MIMapping, self).__setitem__(key, val)
        for i, v in zip(names[1:], values[1:]):
            indices[i][v] = key

    else:
        key1 = item[0]
        item2 = list(item)  # copy item first
        mset_list(item2, index2_list, value)
        key2 = item2[0]
        val = item2[1] if len(item2) == 2 else item2[1:]
        if key1 == key2:
            super(MIMapping, self).__setitem__(key1, val)
        else:
            od_replace_key(self, key1, key2, val)

        for i, v_old, v_new in zip(names[1:], item[1:], item2[1:]):
            od_replace_key(indices[i], v_old, v_new, key2)


def _mid_init(self, *args, **kw):
    '''
    Separate __init__ function of MIMapping
    '''

    items, names = [], None

    n_args = len(args)

    if n_args >= 1:
        items = args[0]

        if isinstance(items, Mapping):  # copy from dict
            if isinstance(items, MIMapping):
                names = items.indices.keys()  # names may be overwritten by second arg
            items = items.items()
        else:  # try to get data from items() or keys() method
            if hasattr(items, 'items'):
                try:
                    items = items.items()
                except TypeError:  # items() may be not callalbe
                    if hasattr(items, 'keys'):
                        try:
                            items = [(k, items[k]) for k in items.keys()]
                        except TypeError:
                            pass

    if n_args >= 2:
        names = args[1]

    if n_args >= 3:
        raise TypeError('At most 2 positional arguments allowed (got %s)' % n_args)

    if items:  # check item length
        n_index = len(items[0])
        for item in items[1:]:
            if len(item) != n_index:
                raise ValueError('Length of all items must equal')
    else:
        n_index = 0

    if kw:
        if n_index == 0:
            n_index = 2
        else:
            if n_index != 2:
                raise ValueError('Number of indices must be 2 (got %s) '
                                 'when keyword arguments are used' % n_index)
        items.extend(kw.items())

    if n_index > 0:
        if names is not None:
            if len(names) != n_index:
                raise ValueError('Length of names (%s) does not match '
                                 'length of items (%s)' % (len(names), n_index))

    if names is None:  # generate default names
        names = ['index_' + str(i) for i in range(n_index)]
    else:
        for name in names:
            if not isinstance(name, (str, unicode)):
                raise TypeError('Index name must be a str or unicode. '
                                'found type %s for %s' % (type(name), name))

    d = self.indices = IdxOrdDict() # the internal dict
    for index in names:
        if index in d:
            raise ValueError('Duplicate index name: %s' % (index,))
        d[index] = AttrOrdDict()

    if n_index > 0:
        d[0] = self
        for item in items:
            primary_key = item[0]
            if n_index == 1:
                value = primary_key
            elif n_index == 2:
                value = item[1]
            else:
                value = list(item[1:])
            # will handle duplicate
            _mid_setitem(self, primary_key, value)


class MIMapping(AttrOrdDict):
    '''
    Base class for all provided multi-index dictionary (MIDict) types.

    Mutable and immutable MIDict types extend this class, which implements
    all the shared logic. Users will typically only interact with subclasses
    of this class.

    '''

    def __init__(self, *args, **kw):
        '''
        Init dictionary with items and index names:

            (items, names, **kw)
            (dict, names, **kw)
            (MIDict, names, **kw)

        ``names`` and ``kw`` are optional.

        ``names`` must all be str or unicode type.
        When ``names`` not present, index names default to: 'index_0', 'index_1', etc.
        When keyword arguments present, only two indices allowed (like a normal dict)


        Example:

            index_names = ['uid', 'name', 'ip']
            rows_of_data = [[1, 'jack', '192.1'],
                            [2, 'tony', '192.2']]

            user = MIDict(rows_of_data, index_names)

            user = MIDict(rows_of_data)
            <==> user = MIDict(rows_of_data, ['index_0', 'index_1', 'index_2'])


        Construct from normal dict:

            normal_dict = {'jack':1, 'tony':2}
            user = MIDict(normal_dict.items(), ['name', 'uid'])
            # user -> MIDict([['tony', 2], ['jack', 1]], ['name', 'uid'])

        '''


        # assign attr `indices` before calling super's __init__()
        self.indices = None  # will be used as the internal dict

        super(MIMapping, self).__init__()

        _mid_init(self, *args, **kw)


    def __getitem__(self, args):
        '''
        get values via multi-indexing
        '''

        return mid_parse_args(self, args)[-1]

    def __setitem__(self, args, value):
        '''
        set values via multi-indexing
        '''
        raise NotImplementedError

    def __delitem__(self, args):
        '''
        delete a key (and the whole item) via multi-indexing
        '''
        raise NotImplementedError

    ############################################

#    def __len__(self): # not changed


    def __eq__(self, other):
        """
        Test for equality with *other*.

        if ``other`` is a regular mapping/dict, compare only order-insensitive keys/values.
        if ``other`` is also a OrderedDict, also compare the order of keys.
        if ``other`` is also a MIDict, also compare the index names.

        """
        if not isinstance(other, Mapping):
            return NotImplemented

        if isinstance(other, MIMapping):
            return (super(MIMapping, self).__eq__(other) and
                self.indices.keys() == other.indices.keys())
        # other Mapping types

        if len(self) != len(other):
            return False
        # equal length

        if len(self.indices) == 0:  # empty index names, empty items
            return True

        if len(self.indices) != 2:
            return False

        return super(MIMapping, self).__eq__(other) # ignore indices

#    def __ne__(self, other): # inherited from OrderedDict
#        return not self == other

    def __lt__(self, other):
        '''
        Check if ``self < other``

        If ``other`` is not a Mapping type, return NotImplemented.

        If ``other`` is a Mapping type, compare in the following order:
            * length of items
            * length of indices
            * convert ``self`` to an OrderedDict or a dict (depends on the type of ``other``)
              and compare it with ``other``
            * index names (only if ``other`` is a MIDict)

        '''
        if not isinstance(other, Mapping):
            return NotImplemented

        if isinstance(other, MIMapping):
            return (super(MIMapping, self).__lt__(other) and
                self.indices.keys() < other.indices.keys())

        len_other_indices = 2 if len(other) else 0

        diff = len(self.indices) - len_other_indices
        if diff < 0:
            return True
        elif diff > 0:
            return False
        # equal indices length

        return super(MIMapping, self).__lt__(other) # ignore indices

    # use __lt__

    def __le__(self, other):
        'self <= other'
        return self < other or self == other

    def __gt__(self, other):
        'self > other'
        return not self <= other

    def __ge__(self, other):
        'self >= other'
        return not self < other

    def __cmp__(self, other):
        'Return negative if self < other, zero if self == other, positive if self > other.'
        if self < other:
            return -1
        if self == other:
            return 0
        return 1

    def __repr__(self, _repr_running={}):
        'repr as "MIDict(items, names)"'
        call_key = id(self), _get_ident()
        if call_key in _repr_running:
            return '<%s(...)>' % self.__class__.__name__
        _repr_running[call_key] = 1
        try:
            try:
                if self.indices:
                    names = self.indices.keys()
                    return '%s(%s, %s)' % (self.__class__.__name__, self.items(), names)
            except AttributeError:  # may not have attr ``indices`` yet
                pass
            return '%s()' % self.__class__.__name__
        finally:
            del _repr_running[call_key]

    def __reduce__(self):
        'Return state information for pickling'
        return self.__class__, (), self.__dict__

    def copy(self):
        'od.copy() -> a shallow copy of od'
        return self.__class__(self)

#    def __sizeof__(self):
#        'not accurate.. '
#        try:
#            from pympler.asizeof import asizeof as getsizeof
#        except ImportError:
#            from sys import getsizeof
#
#        return getsizeof(self)

    def clear(self, clear_indices=False):
        'Remove all items. index names are removed if ``clear_indices==True``.'
        raise NotImplementedError

    @classmethod
    def fromkeys(cls, keys, value=None):
        '''
        Create a new dictionary with keys from ``keys`` and values set to value.

        fromkeys() is a class method that returns a new dictionary. value defaults to None.

        Length of ``keys`` must not exceed one because no duplicate values are allowed.
        '''
        if len(keys) > 1:
            raise ValueError('Length of keys (%s) must not exceed one because '
                             'no duplicate values are allowed' % (len(keys),))
        self = cls()
        if keys:
            self[keys[0]] = value
        return self

    def get(self, key, default=None):
        '''
        Return the value for ``key`` if ``key`` is in the dictionary, else ``default``.
        If ``default`` is not given, it defaults to None, so that this method never
        raises a ``KeyError``.

        Support "multi-indexing" keys
        '''
        try:
            return self[key]
        except KeyError:
            return None

    def __contains__(self, key):
        '''
        Test for the presence of ``key`` in the dictionary.

        Support "multi-indexing" keys
        '''
        try:
            mid_parse_args(self, key, ingore_index2=True, allow_new=False)
            return True
        except KeyError:
            return False

    def has_key(self, key):
        '''
        Test for the presence of ``key`` in the dictionary. has_key() is deprecated
        in favor of ``key in d``.

        Support "multi-indexing" keys
        '''
        return self.__contains__(key)

    ############################################

    # inherited methods from OrderedDict:
    # copy, pop, popitem, setdefault

    def __iter__(self, index=None):
        'Return an iterator through keys in the ``index`` (defaults to the first index)'

        if self.indices:
            if index is None:
                index = 0
            if index == 0:
                # use super otherwise infinite loop of __iter__
                return super(MIMapping, self).__iter__()
            else:
                return iter(self.indices[index])

        else:
            if index is None:
                return iter(())
            else:
                raise KeyError('Index not found (dictionary is empty): %s' % (index,))


    def __reversed__(self, index=None):
        'Return an reversed iterator through keys in the ``index`` (defaults to the first index)'
        if self.indices:
            if index is None:
                index = 0
            if index == 0:
                # use super otherwise infinite loop of __iter__
                return super(MIMapping, self).__reversed__()
            else: # OrderedDict reverse
                return reversed(self.indices[index])

        else:
            if index is None:
                return iter(())
            else:
                raise KeyError('Index not found (dictionary is empty): %s' % (index,))


    def iterkeys(self, index=None):
        'Return an iterator through keys in the ``index`` (defaults to the first index)'
        return self.__iter__(index)

    def keys(self, index=None):
        'Return a copy list of keys in the ``index`` (defaults to the first index)'
        return list(self.iterkeys(index))

    def itervalues(self, index=None):
        '''
        Return an iterator through values in the ``index`` (defaults to all indices
        except the first index).

        When ``index is None``, yielded values depend on the length of indices (``N``):

            * if N <= 1: return
            * if N == 2: yield values in the 2nd index
            * if N > 2: yield values in all indices except the first index
              (each value is a list of ``N-1`` elements)
        '''
        N = len(self.indices)

        if index is None:
            if N <= 1:
                return
            elif N == 2:
                index = 1
            else:
                index = slice(1, None)
        else:
            index = _key_to_index(self.indices.keys(), index)

        multi = not isinstance(index, int)

        for key in self:
            item = mid_get_item(self, key)
            value = mget_list(item, index)
            if multi:
                value = tuple(value)  # convert to tuple
            yield value

    def values(self, index=None):
        '''
        Return a copy list of values in the ``index``.

        See the notes for ``itervalues()``
        '''
        return list(self.itervalues(index))

    def iteritems(self, indices=None):
        'Return an iterator through items in the ``indices`` (defaults to all indices)'
        if indices is None:
            indices = self.indices.keys()
        return self.itervalues(indices)

    def items(self, indices=None):
        'Return a copy list of items in the ``indices`` (defaults to all indices)'
        return list(self.iteritems(indices))

    def update(self, *args, **kw):
        '''
        Update the dictionary
        '''
        raise NotImplementedError

    def viewkeys(self, index=None):
        '''a set-like object providing a view on the keys in ``index``
        (defaults to the first index)'''
        return MIKeysView(self, index)

    def viewvalues(self, index=None):
        '''a set-like object providing a view on the values in ``index``
        (defaults to all indices except the first index)'''
        return MIValuesView(self, index)

    def viewitems(self, index=None):
        '''a set-like object providing a view on the items in ``index``
        (defaults to all indices)'''
        return MIItemsView(self, index)

    def viewdict(self, index_key=None, index_value=None):
        '''a dict-like object providing a view on the keys in ``index_key``
        (defaults to the first index) and values in ``index_value`` (defaults
        to the last index)'''
        return MIDictView(self, index_key, index_value)

    def todict(self, dict_type=dict, index_key=0, index_value=-1):
        '''convert to a specific type of dict using ``index_key`` as keys
        and ``index_value`` as values (discarding index names)'''
        if len(self):
            return dict_type(self.items([index_key, index_value]))
        else:  # empty
            return dict_type()

############################################


class MIDict(MIMapping):
    '''
    A multi-index dictionary (MIDict) with flexible multi-item indexing syntax.

    Multiple indices
    ----------------

    Consider a table-like data set (e.g., a user table):

    +---------+---------+---------+
    |  name   |   uid   |   ip    |
    +=========+=========+=========+
    |  jack   |    1    |  192.1  |
    +---------+---------+---------+
    |  tony   |    2    |  192.2  |
    +---------+---------+---------+

    In each index (i.e., column), elements are unique and hashable (suitable
    for dict keys).

    A multi-index ``user`` dictionary can be constructed with two arguments:
    a list of items (rows of data), and a list of index names::

        user = MIDict([['jack', 1, '192.1'],
                       ['tony', 2, '192.2']],
                      ['name', 'uid', 'ip'])

    Index names are for easy human understanding and indexing, and thus
    must be ``str`` or ``unicode`` type. The indices (and items) are ordered
    in the dictionary. Compatible with a normal dict, the first index (column)
    is the primary index to lookup/index a key, while the rest index or indices
    contain the corresponding key's value or list of values::

        user['jack'] -> [1, '192.1']


    To use any index (column) as the "keys", and other one or more
    indices as the "values", just specify the indices via the advanced
    indexing syntax ``d[index1:key, index2]``, e.g.::

        user['name':'jack', 'uid'] -> 1
        user['ip':'192.1', 'name'] -> 'jack'

    Here, ``index1`` is the single column used as the "keys", and ``key`` is
    an element in ``index1`` to locate the row of record in the table.
    ``index2`` can be one or more columns to specify the value(s) from the row
    of record.


    Multi-item indexing
    -------------------

    For a multi-column data set, it's useful to be able to access multiple
    columns/indices at the same time.

    In the indexing syntax ``d[index1:key, index2]``, both ``index1`` and
    ``index2`` support flexible indexing using an int, tuple, list or slice
    object, which means (see ``IndexDict`` for more details)::

        int -> the index of a key in d.keys()
        tuple/list -> multiple keys or indices of keys or mixture
        slice(key_start, key_stop, step) -> a range of keys
        # key_start and key_stop can be a key or index of a key

    Using the above ``user`` example::

        user['name':'jack', ['uid','ip']] -> [1, '192.1']
        <==> user['name':'jack', [1,2]]
        <==> user['name':'jack', 'uid':]
        <==> user[0:'jack', 1:]


    Convenient indexing shortcuts
    -----------------------------

    Full syntax: ``d[index1:key, index2]``

    Short syntax::

        d[key] <==> d[first_index:key, all_indice_except_first_index]
        d[:key] <==> d[None:key] <==> d[last_index:key, all_indice_except_last_index]
        d[key, index2] <==> d[first_index:key, index2] # only when ``index2`` is a list or slice object
        d[index1:key, index2_1, index2_2, ...] <==> d[index1:key, (index2_1, index2_2, ...)]

    Examples::

        user['jack'] -> [1, '192.1']
        user[:'192.1'] -> ['jack', 1]
        user['jack', :] -> ['jack', 1, '192.1']


    Compatible with normal dict
    ---------------------------

    A MIDict with 2 indices is fully compatible with the normal dict
    or OrderedDict, and can be used as a drop-in replacement of the latter::

        normal_dict = dict(jack=1, tony=2)
        mi_dict = MIDict(jack=1, tony=2)
        <==> mi_dict = MIDict(normal_dict)

        normal_dict -> {'tony': 2, 'jack': 1}
        mi_dict -> MIDict([['tony', 2], ['jack', 1]], ['index_0', 'index_1'])

        # the following equality checks all return True:

        mi_dict == normal_dict
        normal_dict['jack'] == mi_dict['jack'] == 1
        normal_dict.keys() == mi_dict.keys() == ['tony', 'jack']
        normal_dict.values() == mi_dict.values() == [2, 1]


    Bidirectional dict
    ------------------

    With the advanced indexing syntax, a MIDict with 2 indices
    can be used as a normal dict, as well as a convenient
    **bidirectional dict** to index using either a key or a value::

        mi_dict = MIDict(jack=1, tony=2)

    * Forward indexing (``d[key] -> value``, like a normal dict)::

          mi_dict['jack'] -> 1
          <==> mi_dict[0:'jack', 1]

    * Backward indexing (``d[:value] -> key``)::

          mi_dict[:1] -> 'jack'
          <==> mi_dict[-1:1, 0]


    Attributes as keys
    ------------------

    Use the attribute syntax to access a key in MIDict if it is a valid
    Python identifier (``d.key`` <==> d['key'])::

        mi_dict.jack <==> mi_dict['jack']

    This feature is supported by ``AttrDict``.

    Note that it treats an attribute as a dictionary key only when it can not
    find a normal attribute with that name. Thus, it is the programmer's
    responsibility to choose the correct syntax while writing the code.


    Extended methods for multi-indices
    ----------------------------------

    A series of methods are extended to accept an optional agrument to specify
    which index/indices to use, including ``keys()``, ``values()``, ``items()``,
    ``iterkeys()``, ``itervalues()``, ``iteritems()``, ``viewkeys()``, ``viewvalues()``,
    ``viewitems()``, ``__iter__()`` and ``__reversed__()``::

        user = MIDict([['jack', 1, '192.1'],
                       ['tony', 2, '192.2']],
                      ['name', 'uid', 'ip'])

        user.keys() <==> user.keys(0) <==> user.keys('name') -> ['jack', 'tony']
        user.keys('uid') <==> user.keys(1) -> [1, 2]

        user.values() <==> user.values(['uid', 'ip']) -> [[1, '192.1'], [2, '192.2']]
        user.values('uid') -> [1, 2]
        user.values(['name','ip']) -> [['jack', '192.1'], ['tony', '192.2']]

        user.items() <==> user.values(['name', 'uid', 'ip'])
                            -> [['jack', 1, '192.1'], ['tony', 2, '192.2']]
        user.items(['name','ip']) -> [['jack', '192.1'], ['tony', '192.2']]

    MIDict also provides two handy methods ``d.viewdict(index_key, index_value)``
    and ``d.todict(dict_type, index_key, index_value)`` to view it as a normal
    dict or convert it to a specific type of dict using specified indices as
    keys and values.


    Additional APIs to handle indices
    ---------------------------------
    MIDict provides handy APIs (``d.reorder_indices()``, ``d.rename_index()``,
    ``d.add_index()``, ``d.remove_index()``) to handle the indices::

        d = MIDict([['jack', 1], ['tony', 2]], ['name', 'uid'])

        d.reorder_indices(['uid', 'name'])
        d -> MIDict([[1, 'jack'], [2, 'tony']], ['uid', 'name'])

        d.reorder_indices(['name', 'uid']) # change back indices

        d.rename_index('uid', 'userid') # rename one index
        <==> d.rename_index(['name', 'userid']) # rename all indices
        d -> MIDict([['jack', 1], ['tony', 2]], ['name', 'userid'])

        d.add_index(values=['192.1', '192.2'], name='ip')
        d -> MIDict([['jack', 1, '192.1'], ['tony', 2, '192.2']],
                    ['name', 'userid', 'ip'])

        d.remove_index('userid')
        d -> MIDict([['jack', '192.1'], ['tony', '192.2']], ['name', 'ip'])
        d.remove_index(['name', 'ip']) # remove multiple indices
        d -> MIDict() # empty


    Duplicate keys/values handling
    ------------------------------

    The elements in each index of MIDict should be unique.

    When setting an item using syntax ``d[index1:key, index2] = value2``,
    if ``key`` already exists in ``index1``, the item of ``key`` will be updated
    according to ``index2`` and ``value2``. However, if any value of ``value2``
    already exists in ``index2``, a ``ValueExistsError`` will be raised.

    When constructing a MIDict or updating it with ``d.update()``,
    duplicate keys/values are handled in the same way as above with
    the first index treated as ``index1`` and the rest indices treated as ``index2``::

        d = MIDict(jack=1, tony=2)

        d['jack'] = 10 # replace value of key 'jack'
        d['tom'] = 3 # add new key/value
        d['jack'] = 2 # raise ValueExistsError
        d['alice'] = 2 # raise ValueExistsError
        d[:2] = 'jack' # raise ValueExistsError
        d['jack', :] = ['tony', 22] # raise ValueExistsError
        d['jack', :] = ['jack2', 11] # replace item of key 'jack'

        d.update([['alice', 2]]) # raise ValueExistsError
        d.update(alice=2) # raise ValueExistsError
        d.update(alice=4) # add new key/value

        MIDict([['jack',1]], jack=2) # {'jack': 2}
        MIDict([['jack',1], ['jack',2]]) # {'jack': 2}
        MIDict([['jack',1], ['tony',1]]) # raise ValueExistsError
        MIDict([['jack',1]], tony=1) # raise ValueExistsError


    Internal data struture
    ----------------------

    Internally MIDict uses a 3-level ordered dicts ``d.indices`` to store
    the items and indices and keep the order of them::

        d = MIDict([['jack', 1], ['tony', 2]], ['name', 'uid'])

        d.indices ->

        IdxOrdDict([
            ('name', AttrOrdDict([
                ('jack', IdxOrdDict([('name', 'jack'), ('uid', 1)])),
                ('tony', IdxOrdDict([('name', 'tony'), ('uid', 2)])),
            ])),
            ('uid', AttrOrdDict([
                (1, IdxOrdDict([('name', 'jack'), ('uid', 1)])),
                (2, IdxOrdDict([('name', 'tony'), ('uid', 2)])),
            ])),
        ])

    ``d.indices`` also presents an interface to access the indices and items::

        'name' in d.indices -> True
        list(d.indices) -> ['name', 'uid']
        d.indices.keys() -> ['name', 'uid']


        'jack' in d.indices['name'] -> True
        list(d.indices['name']) -> ['jack', 'tony']
        d.indices['name'].keys() -> ['jack', 'tony']

        d.indices['name'].values() -> [
            IdxOrdDict([('name', 'jack'), ('uid', 1)]),
            IdxOrdDict([('name', 'tony'), ('uid', 2)]),
        ]

        d.indices.name.jack.uid # -> 1
        <==> d.indices['name']['jack']['uid']

    However, users should not directly change the keys/values in ``d.indices``,
    otherwise the structure or the references may be broken.
    Use the methods of ``d`` rather than ``d.indices`` to operate the data.


    More examples of advanced indexing
    ----------------------------------

    * Example of two indices (compatible with normal dict)::

        color = MIDict([['red', '#FF0000'], ['green', '#00FF00']],
                       ['name', 'hex'])

        # flexible indexing of short and long versions:

        color.red # -> '#FF0000'
        <==> color['red']
        <==> color['name':'red']
        <==> color[0:'red'] <==> color[-2:'red']
        <==> color['name':'red', 'hex']
        <==> color[0:'red', 'hex'] <==> color[-2:'red', 1]

        color[:'#FF0000'] # -> 'red'
        <==> color['hex':'#FF0000']
        <==> color[1:'#FF0000'] <==> color[-1:'#FF0000']
        <==> color['hex':'#FF0000', 'name'] <==> color[1:'#FF0000', 0]


        # setting an item using different indices/keys:

        color.blue = '#0000FF'
        <==> color['blue'] = '#0000FF'
        <==> color['name':'blue'] = '#0000FF'
        <==> color['name':'blue', 'hex'] = '#0000FF'
        <==> color[0:'blue', 1] = '#0000FF'

        <==> color[:'#0000FF'] = 'blue'
        <==> color[-1:'#0000FF'] = 'blue'
        <==> color['hex':'#0000FF'] = 'blue'
        <==> color['hex':'#0000FF', 'name'] = 'blue'
        <==> color[1:'#0000FF', 0] = 'blue'

        # result:
        # color -> MIDict([['red', '#FF0000'],
                           ['green', '#00FF00'],
                           ['blue', '#0000FF']],
                          ['name', 'hex'])


    * Example of three indices::

        user = MIDict([[1, 'jack', '192.1'],
                       [2, 'tony', '192.2']],
                      ['uid', 'name', 'ip'])

        user[1]                     -> ['jack', '192.1']
        user['name':'jack']         -> [1, '192.1']
        user['uid':1, 'ip']         -> '192.1'
        user[1, ['name','ip']]      -> ['jack', '192.1']
        user[1, ['name',-1]]        -> ['jack', '192.1']
        user[1, [1,1,0,0,2,2]]      -> ['jack', 'jack', 1, 1, '192.1', '192.1']
        user[1, :]                  -> [1, 'jack', '192.1']
        user[1, ::2]                -> [1, '192.1']
        user[1, 'name':]            -> ['jack', '192.1']
        user[1, 0:-1]               -> [1, 'jack']
        user[1, 'name':-1]          -> ['jack']
        user['uid':1, 'name','ip']  -> ['jack', '192.1']
        user[0:3, ['name','ip']] = ['tom', '192.3'] # set a new item
        # result:
        # user -> MIDict([[1, 'jack', '192.1'],
                          [2, 'tony', '192.2'],
                          [3, 'tom', '192.3']],
                         ['uid', 'name', 'ip'])


    '''

    def __setitem__(self, args, value):
        '''
        set values via multi-indexing

        int/slice syntax can only change values of existing keys, not creating new keys

        If ``d.indices`` is empty (i.e., no index names are set), index names
        can be created when setting a new item with specified names:

            d = MIDict()
            d['uid':1, 'name'] = 'jack'
            # d -> MIDict([[1, 'jack']], ['uid', 'name'])

        If ``d.indices`` is not empty, when setting a new item, all indices and values
        must be specified:

            d = MIDict([['jack', 1, '192.1']], ['name', 'uid', 'ip'])
            d['tony'] = [2, '192.2']
            <==> d['name':'tony',['uid', 'ip']] = [2, '192.2']
            # the following will not work:
            d['alice', ['uid']] = [3] # raise ValueError

        More examles::

            d = MIDict(jack=1, tony=2)

            d['jack'] = 10 # replace value of key 'jack'
            d['tom'] = 3 # add new key/value
            d['jack'] = 2 # raise ValueExistsError
            d['alice'] = 2 # raise ValueExistsError
            d[:2] = 'jack' # raise ValueExistsError
            d['jack', :] = ['tony', 22] # raise ValueExistsError
            d['jack', :] = ['jack2', 11] # replace item of key 'jack'

        '''
        return _mid_setitem(self, args, value)

    def __delitem__(self, args):
        '''
        delete a key (and the whole item) via multi-indexing
        '''
        item = mid_parse_args(self, args, ingore_index2=True)
        for i, v in enumerate(item):
            if i == 0:
                super(MIMapping, self).__delitem__(v)
            else:
                del self.indices[i][v]

    def clear(self, clear_indices=False):
        'Remove all items. index names are removed if ``clear_indices==True``.'
        super(MIMapping, self).clear()
        if clear_indices:
            self.indices.clear()
        else:
            for index_d in self.indices[1:]:
                index_d.clear()

    def update(self, *args, **kw):
        '''
        Update the dictionary with items and names:

            (items, names, **kw)
            (dict, names, **kw)
            (MIDict, names, **kw)

        Optional positional argument ``names`` is only allowed when ``self.indices``
        is empty (no indices are set yet).
        '''
        if len(args) > 1 and self.indices:
            raise ValueError('Only one positional argument is allowed when the'
                             'index names are already set.')

        if not self.indices:  # empty; init again
            _mid_init(self, *args, **kw)
            return

        d = MIMapping(*args, **kw)
        if not d.indices:
            return

        names = self.indices.keys()

        if len(d.indices) != len(names):
            raise ValueError('Length of update items (%s) does not match '
                             'length of original items (%s)' %
                             (len(d.indices), len(names)))

        for key in d:
            # use __setitem__() to handle duplicate
            self[key] = d[key]

#        primary_index = names[0]
#
#        for item in d.items():
#            item_d = IdxOrdDict(zip(names, item))
#
#            for index, value in zip(names, item):
#                index_d = self.indices[index]
#                if value in index_d:
#                    if index == primary_index:  # primary key; replace item
#                        item_d_old = index_d[value]
#                        item_old = item_d_old.values()
#                        for n, v_old, v_new in zip(names[1:], item_old[1:], item[1:]):
#                            if v_new in self.indices[n] and v_new != v_old:
#                                raise ValueError('Partially duplicate items not allowed: '
#                                                 '%s and %s' %
#                                                 (self.indices[n][v_new].values(), item))
#
#                        item_d_old[names] = item  # update to new values
#                        for n, v_old, v_new in zip(names[1:], item_old[1:], item[1:]):
#                            od_replace_key(self.indices[n], v_old, v_new)
#                        break  # finished updating this item
#
#                    else:  # not in primary_index
#                        raise ValueExistsError(value, index)
#            else:  # no break; valid item_d
#                for index, value in zip(names, item):
#                    self.indices[index][value] = item_d

    ############################################
    # additional methods to handle index

    def rename_index(self, *args):
        '''change the index name(s).

        * call with one argument:
            1. list of new index names (to replace all old names)

        * call with two arguments:
            1. old index name(s) (or index/indices)
            2. new index name(s)
        '''
        if len(args) == 1:
            new_indices = args[0]
            old_indices = self.indices.keys()
        else:
            old_indices, new_indices = args
            old_indices, single = convert_index_keys(self.indices, old_indices)
            if single:
                old_indices, new_indices = [old_indices], [new_indices]

        if len(new_indices) != len(old_indices):
            raise ValueError('Length of update indices (%s) does not match '
                             'existing indices (%s)' %
                             (len(new_indices), len(old_indices)))

        map(_check_index_name, new_indices)

        if len(new_indices) != len(set(new_indices)):
            raise ValueError('New indices names are not unique: %s' % (new_indices,))

        od_replace_key(self.indices, old_indices, new_indices, multi=True)


    def reorder_indices(self, indices_order):
        'reorder all the indices'
        # allow mixed index syntax like int
        indices_order, single = convert_index_keys(self.indices, indices_order)
        old_indices = self.indices.keys()

        if indices_order == old_indices: # no changes
            return

        if set(old_indices) != set(indices_order):
            raise KeyError('Keys in the new order do not match existing keys')

        if len(old_indices) == 0:
            return

        # must have more than 1 index to reorder
        new_idx = [old_indices.index(i) for i in indices_order]
        # reorder items
        items = [map(i.__getitem__, new_idx) for i in self.items()]
        self.clear(True)
        _mid_init(self, items, indices_order)


    def add_index(self, values, name=None):
        'add an index of ``name`` with the list of ``values``'
        if len(values) != len(set(values)):
            raise ValueError('Values in the new index are not unique')

        d = self.indices
        if len(values) != len(self) and len(values) and d:
            raise ValueError('Length of values in added index (%s) does not match '
                             'length of existing items (%s)' % (len(values), len(self)))

        if name is None:
            name = 'index_' + str(len(d))
            name = _get_unique_name(name, d)
        else:
            _check_index_name(name)
            if name in d:
                raise ValueError('Duplicate index name: %s' % (name,))

        if len(d) == 0:
            items = [(v,) for v in values]
        else:
            items = [i+(v,) for i, v in zip(self.items(), values)]

        names = d.keys() + [name]

        self.clear(True)
        _mid_init(self, items, names)


    def remove_index(self, index):
        'remove one or more indices'
        index_rm = _key_to_index(self.indices.keys(), index)
        if isinstance(index_rm, int):
            index_rm = [index_rm]

        index_new = [i for i in range(len(self.indices)) if i not in index_rm]

        if not index_new: # no index left
            self.clear(True)
            return

        names = mget_list(self.indices.keys(), index_new)
        items = [mget_list(i, index_new) for i in self.items()]
        self.clear(True)
        _mid_init(self, items, names)


############################################


class FrozenMIDict(MIMapping, Hashable):
    """Immutable, hashable multi-index dictionary"""

    def __init__(self, *args, **kw):
        # set _hash as a normal attribute before init
        self._hash = None

        super(FrozenMIDict, self).__init__(*args, **kw)

    def __hash__(self):
        """Return the hash of this bidict."""
        if self._hash is None:
            self._hash = hash((frozenset(self.viewitems()), frozenset(
                self.indices.viewkeys())))
        return self._hash

############################################


class MIKeysView(KeysView):
    '''a set-like object providing a view on the keys in ``index``
    (defaults to the first index)'''

    def __init__(self, mapping, index=None):
        if index is not None and index not in mapping.indices:
            raise KeyError('Index not found: %s' % (index,))
        self.index = index
        super(MIKeysView, self).__init__(mapping)

    def __contains__(self, key):
        if self._mapping.indices:
            index = self.index
            if index is None:
                index = 0
            return key in self._mapping.indices[index]
        else:
            return False

    def __iter__(self):
        return self._mapping.iterkeys(self.index)


class MIValuesView(ValuesView):
    '''a set-like object providing a view on the values in ``index``
    (defaults to all indices except the first index)'''

    def __init__(self, mapping, index=None):
        if index is not None and index not in mapping.indices:
            raise KeyError('Index not found: %s' % (index,))
        self.index = index
        super(MIValuesView, self).__init__(mapping)

    def __contains__(self, value):
        for v in self:
            if value == v:
                return True
        return False

    def __iter__(self):
        return self._mapping.itervalues(self.index)


class MIItemsView(ItemsView):
    '''a set-like object providing a view on the items in ``index``
    (defaults to all indices)'''

    def __init__(self, mapping, index=None):
        if index is not None and index not in mapping.indices:
            raise KeyError('Index not found: %s' % (index,))
        self.index = index
        super(MIItemsView, self).__init__(mapping)

    def __contains__(self, item):
        for v in self:
            if item == v:
                return True
        return False

    def __iter__(self):
        return self._mapping.iteritems(self.index)


class MIDictView(KeysView):
    '''a dict-like object providing a view on the keys in ``index_key``
    (defaults to the first index) and values in ``index_value`` (defaults
    to the last index)'''

    def __init__(self, mapping, index_key=None, index_value=None):
        for index in [index_key, index_value]:
            if index is not None and index not in mapping.indices:
                raise KeyError('Index not found: %s' % (index,))
        self.index_key = index_key
        self.index_value = index_value
        super(MIDictView, self).__init__(mapping)

    def __contains__(self, key):
        if self._mapping.indices:
            index = self.index_key
            if index is None:
                index = 0
            return key in self._mapping.indices[index]
        else:
            return False

    def __iter__(self):
        return self._mapping.iterkeys(self.index_key)

    def iterkeys(self):
        return iter(self)

    def itervalues(self):
        return self._mapping.iterkeys(self.index_value)

    def iteritems(self):
        if self._mapping.indices:
            return self._mapping.iteritems([
                0 if self.index_key is None else self.index_key,
                -1 if self.index_value is None else self.index_value])
        else:
            return iter(())

    def keys(self):
        return list(self.iterkeys())

    def values(self):
        return list(self.itervalues())

    def items(self):
        return list(self.iteritems())

    def __repr__(self):
        return ('{0.__class__.__name__}({0._mapping!r}, index_key={0.index_key}, '
                'index_value={0.index_value})').format(self)

############################################


class MIDictError(Exception):
    'Base class for MIDict exceptions'
    pass


class ValueExistsError(KeyError, MIDictError):
    '''
    Value already exists in an index and can not be used as a key.

    Usage::

        ValueExistsException(value, index)
    '''

    def __str__(self):
        """Get a string representation of this exception for use with str."""
        return 'Value {0!r} exists in index {1!r}'.format(*self.args)

############################################


def test():
    m = IdxOrdDict(a=1, b=2)
    m['a'] = 10
    m['a', 'b'] = [10, 20]
    tuple_key = 'a', 'b', 'c'
    m[tuple_key] = [10, 20]
    m[tuple_key,] = 0,

    d = MIDict([[1, 'jack', ('192.100', 81)], [2, 'tony', ('192.100', 82)]],
               ['uid', 'name', 'ip'])

    d
    d[1]
    #    d[1, 'name']
    d[1, ['name', 'ip']]

    d[:('192.100', 81)]
    d['uid':2, 'name']
    d['uid':2, 'name', 'ip']
    d['uid':2, ['name', 'ip']]
    d['uid':2, 'name':'ip']
    d['uid':2, 'uid':'ip']
    d['uid':2, 0:9]
    d['uid':2, 'uid':9]
    d['uid':2, 'uid':]
    d['uid':2, :9]
    d['uid':2, :]
    d['uid':2, ::2]
    d.indices.uid[1].name
    len(d)
    d.rename_index(['a', 'b', 'c'])

    d = MIDict()
    # init like this:
    d[:'jack', 'uid'] = 1

    d['uid':2, 'name'] = 'jack'
    d['a'] = 1
    d.b = 20
    d[:1] = 'a'
    d[:3] = 'c'
    d.rename_index(['uid', 'name'])
    d.rename_index(['a', 'b'])
    d['uid':2] = 'jack'
    d['uid':2, 'name'] = 'jack'
    d.rename_index('uid', 'a')

    from pympler.asizeof import asizeof as getsizeof

    od = OrderedDict(a=1, b=2)

    d = MIDict([[1, 'jack'], [2, 'tony'], [3, 'tom']], ['uid', 'name'])

    d = FrozenMIDict([[1, 'jack'], [2, 'tony'], [3, 'tom']], ['uid', 'name'])

    print getsizeof(od)
    print getsizeof(d)
    print getsizeof(d.indices)
    print getsizeof(d.indices[0])
    print getsizeof(d.indices[-1])
    print getsizeof(d.indices[0].values()[0])
    '''
408
488
1136
488
488
48
    '''
