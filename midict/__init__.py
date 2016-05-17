# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function #, unicode_literals

import sys

__version__ = '0.1.1'


PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

from collections import Hashable, ItemsView, KeysView, Mapping, OrderedDict, ValuesView

NoneType = type(None)

if PY2:
    from threading import _get_ident
    string_types = str, unicode
else:
    from threading import get_ident as _get_ident
    string_types = str, bytes
    _map = map
    map = lambda *args: list(_map(*args)) # always return a list


#==============================================================================
# auxiliary functions
#==============================================================================

def force_list(a):
    '''convert an iterable ``a`` into a list if it is not a list.'''
    if isinstance(a, list):
        return a
    return list(a)

def cvt_iter(a):
    '''
    Convert an iterator/generator to a tuple so that it can be iterated again.

    E.g., convert zip in PY3.
    '''
    if a is None:
        return a

    if not isinstance(a, (tuple, list)):
        # convert iterator/generator to tuple
        a = tuple(a)
    return a


#==============================================================================
# AttrDict
#==============================================================================

class AttrDict(dict):
    '''
    A dictionary that can get/set/delete a key using the attribute syntax
    if it is a valid Python identifier. (``d.key`` <==> ``d['key']``)

    Note that it treats an attribute as a dictionary key only when it can not
    find a normal attribute with that name. Thus, it is the programmer's
    responsibility to choose the correct syntax while writing the code.

    Be aware that besides all the inherited attributes, AttrDict has an
    additional internal attribute "_AttrDict__attr2item".

    Examples::

        d = AttrDict(__init__='value for key "__init__"')
        d.__init__ -> <bound method AttrDict.__init__>
        d["__init__"] -> 'value for key "__init__"'

    '''

    def __init__(self, *args, **kw):
        '''Init the dict using the same arguments for ``dict``.

        set any attributes here (or in subclass) - before __init__()
        so that these remain as normal attributes
        '''
        super(AttrDict, self).__init__(*args, **kw)

        # last line of code in __init__()
        self.__attr2item = True # transfered to _AttrDict__attr2item

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



def convert_dict(d, cls=AttrDict): # not used
    '''
    recursively convert a normal Mapping `d` and it's values to a specified type
    (defaults to AttrDict)
    '''
    for k, v in d.items():
        if isinstance(v, Mapping):
            d[k] = convert_dict(v)
        elif isinstance(v, list):
            for i, e in enumerate(v):
                if isinstance(e, Mapping):
                    v[i] = convert_dict(e)
    return cls(d)



#==============================================================================
# IndexDict
#==============================================================================


def _key_to_index(keys, key, single_only=False):
    'convert ``key`` of various types to int or list of int'
    if isinstance(key, int): # validate the int index
        try:
            keys[key]
        except IndexError:
            raise KeyError('Index out of range of keys: %s' % (key,))
        if key < 0:
            key += len(keys) # always positive index
        return key
#    keys = d.keys()
    if not single_only:
        if isinstance(key, (tuple, list)):
            return [_key_to_index_single(keys, k) for k in key]

        if isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
            try:
                MI_check_index_name(start)
                start = keys.index(start)
            except TypeError:
                pass
            try:
                MI_check_index_name(stop)
                stop = keys.index(stop)
            except TypeError:
                pass
#            return slice(start, stop, step)
            args = slice(start, stop, step).indices(len(keys))
            return force_list(range(*args)) # list of indices
    try:
        return keys.index(key)
    except ValueError: # not IndexError
        raise KeyError('Key not found: %s' % (key,))


def _key_to_index_single(keys, key):
    return _key_to_index(keys, key, single_only=True)


def convert_key_to_index(keys, key):
    '''
    convert ``key`` of various types to int or list of int

    return index, single
    '''
    index = _key_to_index(keys, key)
    single = isinstance(index, int)
    return index, single


def _int_to_key(keys, index):
    'Convert int ``index`` to the corresponding key in ``keys``'
    if isinstance(index, int):
        try:
            return keys[index]
        except IndexError:
            # use KeyError rather than IndexError for compatibility
            raise KeyError('Index out of range of keys: %s' % (index,))
    return index


def convert_index_to_keys(d, item):
    # use a separate function rather than a method inside the class IndexDict
    '''
    Convert ``item`` in various types (int, tuple/list, slice, or a normal key)
    to a single key or a list of keys.
    '''

    keys = force_list(d.keys())
    # use KeyError for compatibility of normal use

    # Warning: int item will be interpreted as the index rather than key!!
    if isinstance(item, int):
        item = _int_to_key(keys, item)
        single = True

    elif isinstance(item, (tuple, list)):
        item2 = []
        for i in item:
            i = _int_to_key(keys, i)
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
        IndexDict_check_key_type(item)
        single = True

    return item, single


def IndexDict_check_key_type(key):
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
        type       content of the ``item`` argument   corresponding values
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


    Examples::

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
        super(IndexDict, self).__init__()
        if args:
            # if args[0] is an iterator (eg zip in PY3)
            # args[0] can only be iterated once
            for key, value in args[0]:
                IndexDict_check_key_type(key)
                self[key] = value
        self.update(**kw)

    def __getitem__(self, item):
        '''
        Get one or more items using flexible indexing.
        '''
        item2, single = convert_index_to_keys(self, item)
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
        item2, single = convert_index_to_keys(self, item)
        super_setitem = super(IndexDict, self).__setitem__
        if single:
            super_setitem(item2, value)
        else:
            if len(item2) != len(value):
                raise ValueError(
                    'Number of keys (%s) based on argument %s does not match '
                    'number of values (%s)' % (len(item2), item, len(value)))
            map(IndexDict_check_key_type, item2)
            return map(super_setitem, item2, value)

    def __delitem__(self, item):
        '''
        Delete one or more items using flexible indexing.
        '''
        item2, single = convert_index_to_keys(self, item)
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
    '''
    AttrDict + OrderedDict
    '''


class IdxOrdDict(IndexDict, AttrDict, OrderedDict):
    '''
    IndexDict + AttrDict + OrderedDict
    '''


#==============================================================================
# MIMapping
#==============================================================================


class MIMappingError(Exception):
    'Base class for MIDict exceptions'
    pass


class ValueExistsError(KeyError, MIMappingError):
    '''
    Value already exists in an index and can not be used as a key.

    Usage::

        ValueExistsException(value, index_order, index_name)
    '''

    def __str__(self):
        """Get a string representation of this exception for use with str."""
        return 'Value {0!r} already exists in index #{1}: {2!r}'.format(*self.args)


#==============================================================================


def MI_check_index_name(name):
    'Check if index name is a valid str or unicode'
    if not isinstance(name, string_types):
        raise TypeError('Index name must be a string. '
                        'Found type %s for %s' % (type(name), name))


def get_unique_name(name='', collection=()):
    '''
    Generate a unique name (str type) by appending a sequence number to
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


def get_value_len(value):
    '''
    Get length of ``value``. If ``value`` (eg, iterator) has no len(), convert it to list first.

    return both length and converted value.
    '''
    try:
        Nvalue = len(value)
    except TypeError:
        # convert iterator/generator to list
        value = list(value)
        Nvalue = len(value)
    return Nvalue, value


def MI_parse_args(self, args, ingore_index2=False, allow_new=False):
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

    names = force_list(self.indices.keys())

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

            # args[0] is not a slice
            if Nargs > 1 and isinstance(args[1], (list, slice)):
                if Nargs == 2:
                    key, index2 = args
                    break
                else:
                    raise KeyError('No arguments allowed after index2, found: %s' % (args[2:],))
        else:
            key = args

    elif isinstance(args, slice):
        index1, key = args.start, args.stop

    else:
        key = args

    if empty: # allow_new is True
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
                MI_check_index_name(index1)
                exist_names.append(index1)
        if index2 is not _default:
            if isinstance(index2, (tuple, list)):
                map(MI_check_index_name, index2)
                exist_names.extend(index2)
            elif isinstance(index2, (int, slice)):
                raise TypeError('Index2 can not be int or slice when '
                                'dictionary is empty: %s' % (index2,))
            else:
                MI_check_index_name(index2)
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
            index1 = get_unique_name(name1, exist_names)
            exist_names.append(index1)

        if index2 is _default:
            name2 = 'index_1' if index1_last else 'index_2'
            index2 = get_unique_name(name2, exist_names)

        return index1, key, index2, index1_last

    # not empty:

    if index1 is _default:  # not specified
        index1 = 0
    elif index1 is None:  # slice syntax d[:key]
        index1 = -1

    # index1 is always returned as an int
    index1 = _key_to_index_single(names, index1)

    try:
        item = MI_get_item(self, key, index1)
    except KeyError:
        if allow_new:  # new key for setitem; item_d = None
            item = None
        else:
            raise KeyError('Key not found in index #%s "%s": %s' %
                            (index1, names[index1], key))

    if ingore_index2:  # used by delitem
        return item

    if index2 is _default:  # not specified
        # index2 defaults to all indices except index1
        if len(names) == 1:
            index2 = 0  # index2 defaults to the only one index
        else:
            index2 = force_list(range(len(names)))
            index2.remove(index1)
            if len(index2) == 1:  # single index
                index2 = index2[0]
    else:
        # index2 is always returned as int or list of int
        index2 = _key_to_index(names, index2)

    if item is None:  # allow_new. item and value are None
        return index1, key, index2, None, None

#    try:
#        value = mget_list(item, index2)
#    except IndexError:
#        raise KeyError('Index not found: %s' % (index2,))

    # no need to try since index2 is always returned as int or list of int
    value = mget_list(item, index2)
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
        map(item.__setitem__, index, value)


def MI_get_item(self, key, index=0):
    'return list of item'
    index = _key_to_index_single(force_list(self.indices.keys()), index)
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

    # single key

    if args:
        value = args[0]

    if new_key == key:
        if args:
            OrderedDict.__setitem__(od, key, value)
        return

    # new_key != key
    if new_key in od: # new_key overwrites another existing key
        OrderedDict.__delitem__(od, new_key)

    if PY2:
        # modify internal variables
        _map = od._OrderedDict__map
        link = _map[key]
        link[2] = new_key
        del _map[key]
        _map[new_key] = link
        val = dict.pop(od, key)
        if args:
            val = value
        dict.__setitem__(od, new_key, val)

    else:
        # in PY3, OrderedDict is implemented in C
        # no access to private variables __map
        found = False
        keys = [] # keys after key
        for k in od:
            if k == key:
                found = True
                continue
            if found:
                keys.append(k)
        # warning: can not use OrderedDict.pop, which calls del self[key]
        getitem = dict.__getitem__
        setitem = OrderedDict.__setitem__
        delitem = OrderedDict.__delitem__
        v = getitem(od, key)
        delitem(od, key)
        if args:
            v = value
        setitem(od, new_key, v)
        # shift keys to after new_key
        for k in keys:
            # od[k] = od.pop(k) # can not call this directly in MIDict
            v = getitem(od, k)
            delitem(od, k)
            setitem(od, k, v)


def od_reorder_keys(od, keys_in_new_order): # not used
    '''
    Reorder the keys in an OrderedDict ``od`` in-place.
    '''
    if set(od.keys()) != set(keys_in_new_order):
        raise KeyError('Keys in the new order do not match existing keys')
    for key in keys_in_new_order:
        od[key] = od.pop(key)
    return od


def _MI_setitem(self, args, value):
    'Separate __setitem__ function of MIMapping'
    indices = self.indices
    N = len(indices)
    empty = N == 0
    if empty: # init the dict
        index1, key, index2, index1_last = MI_parse_args(self, args, allow_new=True)
        exist_names = [index1]
        item = [key]
        try:
            MI_check_index_name(index2)
            exist_names.append(index2)
            item.append(value)
        except TypeError:
            Nvalue, value = get_value_len(value)
            if len(index2) != Nvalue:
                raise ValueError(
                    'Number of keys (%s) based on argument %s does not match '
                    'number of values (%s)' % (len(index2), index2, Nvalue))
            exist_names.extend(index2)
            item.extend(value)
        if index1_last:
            exist_names = exist_names[1:] + exist_names[:1]
            item = item[1:] + item[:1]

        _MI_init(self, [item], exist_names)
        return

    index1, key, index2, item, old_value = MI_parse_args(self, args, allow_new=True)
    names = force_list(indices.keys())
    is_new_key = item is None
    single = isinstance(index2, int)

    if single:
        index2_list = [index2]
        value = [value]
        old_value = [old_value]
    else:
        index2_list = index2
        Nvalue, value = get_value_len(value)
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
                raise ValueExistsError(v, i, names[i])

    if is_new_key:
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

    else: # not new key
#        import pdb;pdb.set_trace()
        key1 = item[0]
        item2 = list(item)  # copy item first
        mset_list(item2, index2_list, value) # index2_list may also override index1
        key2 = item2[0]
        val = item2[1] if len(item2) == 2 else item2[1:]
        if key1 == key2:
            super(MIMapping, self).__setitem__(key1, val)
        else:
            od_replace_key(self, key1, key2, val)

        for i, v_old, v_new in zip(names[1:], item[1:], item2[1:]):
            od_replace_key(indices[i], v_old, v_new, key2)


def _MI_init(self, *args, **kw):
    '''
    Separate __init__ function of MIMapping
    '''

    items, names = [], None

    n_args = len(args)

    if n_args >= 1:
        items = args[0]

        if isinstance(items, Mapping):  # copy from dict
            if isinstance(items, MIMapping):
                names = force_list(items.indices.keys())  # names may be overwritten by second arg
            items = force_list(items.items())
        else:  # try to get data from items() or keys() method
            if hasattr(items, 'items'):
                try:
                    items = force_list(items.items())
                except TypeError:  # items() may be not callalbe
                    pass
            else:
                items = cvt_iter(items)

    if n_args >= 2:
        names = args[1] # may be None
        names = cvt_iter(names)

    if n_args >= 3:
        raise TypeError('At most 2 positional arguments allowed (%s given)' % n_args)

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
        names = ['index_%s' % (i+1) for i in range(n_index)] # starts from index_1
    else:
        map(MI_check_index_name, names)

    self.indices = d = IdxOrdDict() # the internal dict
    for index in names:
        if index in d:
            raise ValueError('Duplicate index name: %s in %s' % (index, names))
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
                value = list(item[1:]) # copy
            # will handle duplicate
            _MI_setitem(self, primary_key, value)



def MI_method_PY3(cls):
    '''class decorator to change MIMapping method names for PY3 compatibility'''

    nmspc = cls.__dict__.copy()
    for m in ['__cmp__', 'has_key']:
        nmspc.pop(m)
    methods = ['keys', 'values', 'items']
    for m in methods:
        nmspc[m] = nmspc.pop('view' + m)
    return type(cls)(cls.__name__, cls.__bases__, nmspc)


class MIMapping(AttrOrdDict):
    '''
    Base class for all provided multi-index dictionary (MIDict) types.

    Mutable and immutable MIDict types extend this class, which implements
    all the shared logic. Users will typically only interact with subclasses
    of this class.

    '''

    def __init__(self, *args, **kw):
        '''
        Init dictionary with items and index names::

            (items, names, **kw)
            (dict, names, **kw)
            (MIDict, names, **kw)

        ``names`` and ``kw`` are optional.

        ``names`` must all be str or unicode type.
        When ``names`` not present, index names default to: 'index_0', 'index_1', etc.
        When keyword arguments present, only two indices allowed (like a normal dict)


        Examples::

            index_names = ['uid', 'name', 'ip']
            rows_of_data = [[1, 'jack', '192.1'],
                            [2, 'tony', '192.2']]

            user = MIDict(rows_of_data, index_names)

            user = MIDict(rows_of_data)
            <==> user = MIDict(rows_of_data, ['index_0', 'index_1', 'index_2'])


        Construct from normal dict::

            normal_dict = {'jack':1, 'tony':2}
            user = MIDict(normal_dict.items(), ['name', 'uid'])
            # user -> MIDict([['tony', 2], ['jack', 1]], ['name', 'uid'])

        '''


        # assign attr `indices` before calling super's __init__()
        self.indices = None  # will be used as the internal dict

        super(MIMapping, self).__init__()

        _MI_init(self, *args, **kw)


    def __getitem__(self, args):
        '''
        get values via multi-indexing
        '''

        return MI_parse_args(self, args)[-1]

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
        Test for equality with ``other``.

        if ``other`` is a regular mapping/dict, compare only order-insensitive keys/values.
        if ``other`` is also a OrderedDict, also compare the order of keys.
        if ``other`` is also a MIDict, also compare the index names.

        """
        if not isinstance(other, Mapping):
            return NotImplemented

        is_MIMapping = isinstance(other, MIMapping)
        if not is_MIMapping: # assuming other is a normal 2-index mapping
            if len(self.indices) not in [0,2]:
                return False # indices not equal

        eq = super(MIMapping, self).__eq__(other)

        if not eq:
            return False

        if is_MIMapping:
            eq = force_list(self.indices.keys()) == force_list(other.indices.keys())

        return eq # ignore indices


    def __ne__(self, other): # PY2: inherited from OrderedDict
        return not self == other


    def __lt__(self, other):
        '''
        Check if ``self < other``

        If ``other`` is not a Mapping type, return NotImplemented.

        If ``other`` is a Mapping type, compare in the following order:
            * convert ``self`` to an OrderedDict or a dict (depends on the type of ``other``)
              and compare it with ``other``
            * index names (only if ``other`` is a MIMapping)

        '''
        if not isinstance(other, Mapping):
            return NotImplemented

        if PY2:
            cp = super(MIMapping, self).__cmp__(other) # Python2
            if cp < 0:
                return True
            if cp == 0:
                if isinstance(other, MIMapping):
                    return force_list(self.indices.keys()) < force_list(other.indices.keys())
            return False
        else: # PY3
            raise TypeError('unorderable types %r < %r' % (self, other))


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
        # gone in PY3
        'Return negative if self < other, zero if self == other, positive if self > other.'
        # warning: "<" causes recursion of __cmp__
#        if self < other:
#            return -1
        return NotImplemented

    def __repr__(self, _repr_running={}):
        'repr as "MIDict(items, names)"'
        call_key = id(self), _get_ident()
        if call_key in _repr_running: # pragma: no cover
            return '<%s(...)>' % self.__class__.__name__
        _repr_running[call_key] = 1
        try:
            try:
                if self.indices:
                    names = force_list(self.indices.keys())
                    items = force_list(self.items())
                    return '%s(%s, %s)' % (self.__class__.__name__, items, names)
            except AttributeError: # pragma: no cover
                # may not have attr ``indices`` yet
                pass
            return '%s()' % self.__class__.__name__
        finally:
            del _repr_running[call_key]

    def __reduce__(self):
        'Return state information for pickling'
        items = force_list(self.items())
        names = force_list(self.indices.keys())
        inst_dict = vars(self).copy() # additional state/__dict__
        for k in vars(self.__class__()):
            inst_dict.pop(k, None)
        return self.__class__, (items, names), inst_dict

    def copy(self):
        'a shallow copy'
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
    def fromkeys(cls, keys, value=None, names=None):
        '''
        Create a new dictionary with keys from ``keys`` and values set to ``value``.

        fromkeys() is a class method that returns a new dictionary. ``value`` defaults to None.

        Length of ``keys`` must not exceed one because no duplicate values are allowed.

        Optional ``names`` can be provided for index names (of length 2).
        '''
        N = len(keys)
        if N > 1:
            raise ValueError('Length of keys (%s) must not exceed one because '
                             'no duplicate values are allowed' % (N,))
        items = [[keys[0], value]] if N == 1 else []
        return cls(items, names)

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
            return default

    def __contains__(self, key):
        '''
        Test for the presence of ``key`` in the dictionary.

        Support "multi-indexing" keys
        '''
        try:
            MI_parse_args(self, key, ingore_index2=True, allow_new=False)
            return True
        except Exception:
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
    # pop, popitem, setdefault

    def __iter__(self, index=None):
        'Iterate through keys in the ``index`` (defaults to the first index)'

        if self.indices:
            if index is None:
                index = 0
            if index == 0:
                # use super otherwise infinite loop of __iter__
                for x in super(MIMapping, self).__iter__():
                    yield x
            else:
                for x in self.indices[index]:
                    yield x

        else:
            if index is not None:
                raise KeyError('Index not found (dictionary is empty): %s' % (index,))


    def __reversed__(self, index=None):
        'Iterate in reversed order through keys in the ``index`` (defaults to the first index)'
        if self.indices:
            if index is None:
                index = 0
            if index == 0:
                # use super otherwise infinite loop of __iter__
                for x in super(MIMapping, self).__reversed__(): # from OrderedDict
                    yield x
            else: # OrderedDict reverse
                for x in reversed(self.indices[index]):
                    yield x
        else:
            if index is not None:
                raise KeyError('Index not found (dictionary is empty): %s' % (index,))


    def iterkeys(self, index=None):
        'Iterate through keys in the ``index`` (defaults to the first index)'
        for x in self.__iter__(index):
            yield x

    def keys(self, index=None):
        'Return a copy list of keys in the ``index`` (defaults to the first index)'
        return list(self.iterkeys(index))

    def itervalues(self, index=None):
        '''
        Iterate through values in the ``index`` (defaults to all indices
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
                single = True
            else:
                index = slice(1, None)
                single = False
        else:
            index, single = convert_key_to_index(force_list(self.indices.keys()), index)

        multi = not single

        for key in self:
            item = MI_get_item(self, key)
            value = mget_list(item, index)
            if multi:
                value = tuple(value)  # convert list to tuple
            yield value

    def values(self, index=None):
        '''
        Return a copy list of values in the ``index``.

        See the notes for ``itervalues()``
        '''
        return list(self.itervalues(index))

    def iteritems(self, indices=None):
        'Iterate through items in the ``indices`` (defaults to all indices)'
        if indices is None:
            indices = force_list(self.indices.keys())
        for x in self.itervalues(indices):
            yield x

    def items(self, indices=None):
        'Return a copy list of items in the ``indices`` (defaults to all indices)'
        return force_list(self.iteritems(indices))

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


if PY3: # change method names
    MIMapping = MI_method_PY3(MIMapping)


############################################


class MIDict(MIMapping):
    '''
    MIDict is an ordered "dictionary" with multiple indices
    where any index can serve as "keys" or "values",
    capable of assessing multiple values via its powerful indexing syntax,
    and suitable as a bidirectional/inverse dict (a drop-in replacement
    for dict/OrderedDict in Python 2 & 3).

    **Features**:

    * Multiple indices
    * Multi-value indexing syntax
    * Convenient indexing shortcuts
    * Bidirectional/inverse dict
    * Compatible with normal dict in Python 2 & 3
    * Accessing keys via attributes
    * Extended methods for multi-indices
    * Additional APIs to handle indices
    * Duplicate keys/values handling

    '''

    def __setitem__(self, args, value):
        '''
        set values via multi-indexing

        If ``d.indices`` is empty (i.e., no index names and no items are set), index names
        can be created when setting a new item with specified names (``index1`` and ``index2``
        can not be int or slice)::

            d = MIDict()
            d['uid':1, 'name'] = 'jack'
            # d -> MIDict([[1, 'jack']], ['uid', 'name'])

            d = MIDict()
            d[1] = 'jack' # using default index names
            <==> d[:'jack'] = 1
            # d -> MIDict([(1, 'jack')], ['index_1', 'index_2'])

        If ``d.indices`` is not empty, when setting a new item, all indices of the item
        must be specified via ``index1`` and ``index2`` (implicitly or explicitly)::

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
        return _MI_setitem(self, args, value)

    def __delitem__(self, args):
        '''
        delete a key (and the whole item) via multi-indexing
        '''
        item = MI_parse_args(self, args, ingore_index2=True)
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
        Update the dictionary with items and names::

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
            _MI_init(self, *args, **kw)
            return

        d = MIMapping(*args, **kw)
        if not d.indices:
            return

        names = force_list(self.indices.keys())

        if len(d.indices) != len(names):
            raise ValueError('Length of update items (%s) does not match '
                             'length of original items (%s)' %
                             (len(d.indices), len(names)))

        for key in d:
            # use __setitem__() to handle duplicate
            self[key] = d[key]


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
            old_indices =force_list(self.indices.keys())
        else:
            old_indices, new_indices = args
            old_indices, single = convert_index_to_keys(self.indices, old_indices)
            if single:
                old_indices, new_indices = [old_indices], [new_indices]

        if len(new_indices) != len(old_indices):
            raise ValueError('Length of update indices (%s) does not match '
                             'existing indices (%s)' %
                             (len(new_indices), len(old_indices)))

        map(MI_check_index_name, new_indices)

        if len(new_indices) != len(set(new_indices)):
            raise ValueError('New indices names are not unique: %s' % (new_indices,))

        od_replace_key(self.indices, old_indices, new_indices, multi=True)


    def reorder_indices(self, indices_order):
        'reorder all the indices'
        # allow mixed index syntax like int
        indices_order, single = convert_index_to_keys(self.indices, indices_order)
        old_indices = force_list(self.indices.keys())

        if indices_order == old_indices: # no changes
            return

        if set(old_indices) != set(indices_order):
            raise KeyError('Keys in the new order do not match existing keys')

#        if len(old_indices) == 0: # already return since indices_order must equal to old_indices
#            return

        # must have more than 1 index to reorder
        new_idx = [old_indices.index(i) for i in indices_order]
        # reorder items
        items = [map(i.__getitem__, new_idx) for i in self.items()]
        self.clear(True)
        _MI_init(self, items, indices_order)


    def add_index(self, values, name=None):
        'add an index of ``name`` with the list of ``values``'
        if len(values) != len(set(values)):
            raise ValueError('Values in the new index are not unique')

        d = self.indices
        if len(values) != len(self) and len(values) and d:
            raise ValueError('Length of values in added index (%s) does not match '
                             'length of existing items (%s)' % (len(values), len(self)))

        if name is None:
            name = 'index_' + str(len(d)+1)
            name = get_unique_name(name, d)
        else:
            MI_check_index_name(name)
            if name in d:
                raise ValueError('Duplicate index name: %s' % (name,))

        if len(d) == 0:
            items = [(v,) for v in values]
        else:
            items = [i+(v,) for i, v in zip(self.items(), values)]

        names = force_list(d.keys()) + [name]

        self.clear(True)
        _MI_init(self, items, names)


    def remove_index(self, index):
        'remove one or more indices'
        index_rm, single = convert_key_to_index(force_list(self.indices.keys()), index)
        if single:
            index_rm = [index_rm]

        index_new = [i for i in range(len(self.indices)) if i not in index_rm]

        if not index_new: # no index left
            self.clear(True)
            return

        names = mget_list(force_list(self.indices.keys()), index_new)
        items = [mget_list(i, index_new) for i in self.items()]
        self.clear(True)
        _MI_init(self, items, names)


############################################


class FrozenMIDict(MIMapping, Hashable):
    '''
    An immutable, hashable multi-index dictionary (similar to ``MIDict``).
    '''

    def __init__(self, *args, **kw):
        # set _hash as a normal attribute before init
        self._hash = None

        super(FrozenMIDict, self).__init__(*args, **kw)

    def __hash__(self):
        """Return the hash of this bidict."""
        if self._hash is None:
            self._hash = hash((frozenset(self.items()), frozenset(
                self.indices.keys())))
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
        for x in self._mapping.iterkeys(self.index):
            yield x


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
        for x in self._mapping.itervalues(self.index):
            yield x


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
        for x in self._mapping.iteritems(self.index):
            yield x


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
        for x in self._mapping.iterkeys(self.index_key):
            yield x

    def iterkeys(self):
        for x in self:
            yield x

    def itervalues(self): # single index
        index = self.index_value
        if self._mapping.indices:
            if index is None:
                index = -1
            for x in self._mapping.iterkeys(index):
                yield x
        else:
            if index is not None:
                raise KeyError('Index not found (dictionary is empty): %s' % (index,))

    def iteritems(self):
        if self._mapping.indices:
            items = self._mapping.iteritems([
                0 if self.index_key is None else self.index_key,
                -1 if self.index_value is None else self.index_value])
            for x in items:
                yield x

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

#__all__ = [k for k in globals() if k[:1] != '_']
__all__ = [
 'AttrDict',
 'AttrOrdDict',
 'FrozenMIDict',
 'IdxOrdDict',
 'IndexDict',
 'IndexDict_check_key_type',
 'ItemsView',
 'KeysView',
 'MIDict',
 'MIDictView',
 'MIItemsView',
 'MIKeysView',
 'MIMapping',
 'MIMappingError',
 'MIValuesView',
 'MI_check_index_name',
 'MI_get_item',
 'MI_parse_args',
 'OrderedDict',
 'ValueExistsError',
 'ValuesView',
 'convert_dict',
 'convert_index_to_keys',
 'convert_key_to_index',
 'cvt_iter',
 'force_list',
 'get_unique_name',
 'get_value_len',
 'mget_list',
 'mset_list',
 'od_reorder_keys',
 'od_replace_key',
 ]