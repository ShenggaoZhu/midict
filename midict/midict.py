# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 22:46:14 2016

@author: shenggao
"""

from collections import Mapping, OrderedDict, _get_ident, KeysView, ValuesView, ItemsView
from types import NoneType


def od_replace_key(od, key, new_key, *args, **kw):
    '''
    Replace key(s) in OrderedDict `od` by new key(s) in-place (i.e.,
    preserving the order(s) of the key(s))

    Optional new value(s) for new key(s) can be provided as a positional
    argument (otherwise the old value(s) will be used):

        od_replace_key(od, key, new_key, new_value)

    To replace multiple keys, pass argument `key` as a list instance,
    or explicitly pass a keyword argument `multi=True`:

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
                    'length of new values (%s)' % (len(new_key), len(new_value)))
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




class AttrDict(dict):
    '''
    dict that can get/set/delete items through attributes (eg, `d.key`)
    '''

    def __init__(self, *args, **kw):

        # set any attributes here (or in subclass) - before __init__()
        # these remain as normal attributes

        super(AttrDict, self).__init__(*args, **kw)
        self.__attr2item = True # transfered to _AttrDict__attr2item

    # easy access of items through attributes, e.g., d.key
    def __getattr__(self, item):
        """Maps values to attributes.
        Only called if there *isn't* an attribute with this name
        """
        # Note: hasattr() and dir(self) calls __getattr__() internally

        # Note: this allows normal attributes access in the __init__ method

        if '_AttrDict__attr2item' not in self.__dict__: # slot??
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

#        print '__setattr__', item, value
        super_setattr = super(AttrDict, self).__setattr__

        if '_AttrDict__attr2item' not in self.__dict__: # slot??
            return super_setattr(item, value)

        if item in dir(self): # any normal attributes are handled normally
            return super_setattr(item, value)

        return self.__setitem__(item, value)


    def __delattr__(self, item):
        """Maps attributes to values.
        Only if there *isn't* an attribute with this name
        """
        if item in dir(self): # any normal attributes are handled normally
            super(AttrDict, self).__delattr__(item)
        else:
            self.__delitem__(item)



def convert_index_keys(d, item):
    # use a separate function rather than a method inside the class IndexDict
    '''
    convert `item` in various types to a list of keys.
    `item` can be a single key, a tuple, list or slice.
    slice format: "key_start : key_stop : step"
    the `item` can also be the index of the item.
    setting items using int or slice only supports existing keys, not new keys
    '''

    keys = d.keys()
    # use KeyError for compatibility of normal use

    # int item will be interpreted as the index rather than key!!
    if isinstance(item, int):
        try:
            item = keys[item]
            single = True
        except IndexError:
            raise KeyError('Index out of range of keys: %s' % (item,))

    elif isinstance(item, (tuple, list)):
        item2 = []
        for i in item:
            if isinstance(i, int):
                try:
                    i = keys[i]
                except IndexError:
                    raise KeyError('Index out of range of keys: %s' % (i,))
            item2.append(i)
        item = item2
        single = False

    elif isinstance(item, slice):
        start, stop, step = item.start, item.stop, item.step
        # None is not interpreted as a key
        if not isinstance(start, (NoneType,int)):
            try:
                start = keys.index(start)
            except ValueError:
                raise KeyError('%s is not in the list of keys' % (start,))
        if not isinstance(stop, (NoneType,int)):
            try:
                stop = keys.index(stop)
            except ValueError:
                raise KeyError('%s is not in the list of keys' % (stop,))
        item = keys[start:stop:step]
        single = False

    else: # other types, treated as a single key
        single = True

    return item, single



def _check_IndexDict_key(key):
    'raise TypeError if `key` is int, tuple or NoneType'
    if isinstance(key, (int, tuple, NoneType)):
        raise TypeError('Key must not be int or tuple or None: %s' % (key,))


class IndexDict(dict):
    # similar to MultiDict, but not subclass of it
    '''
    A dict of non-int type keys that can use a key (not int type)
    or the index of one or more keys (int or slice type) to
    get/set/delete the value(s).
    '''

    def __init__(self, *args, **kw):
        'check key is not int type'
        if args:
            for key, value in args[0]:
                _check_IndexDict_key(key)
        super(IndexDict, self).__init__(*args, **kw)

#
    def __getitem__(self, item):
        '''get item using key (not int type) or index of key (int or slice type).
        d[key] -> value
        d[index_of_key] -> value
        '''
        item2, single = convert_index_keys(self, item)
        super_getitem = super(IndexDict, self).__getitem__
        if single:
            return super_getitem(item2)
        else:
            return map(super_getitem, item2)



    def __setitem__(self, item, value):
        '''set item using key (not int type) or index of key (int or slice type).
        d[existing_key] = value
        d[not_existing_key] = value # assign value to a new key

        d[index_of_existing_key] = value

        A KeyError will raise if the key does not already exist:

        d[index_of_not_existing_key] = value -> KeyError
        '''
        item2, single = convert_index_keys(self, item)
        super_setitem = super(IndexDict, self).__setitem__
        if single:
            super_setitem(item2, value)
        else:
            if len(item2) != len(value):
                raise ValueError('Number of keys (%s) based on argument %s does not match '
                    'number of values (%s)' % (len(item2), item, len(value)))
            map(_check_IndexDict_key, item2)
            return map(super_setitem, item2, value)


    def __delitem__(self, item):
        '''
        delete item using key (not int type) or index of key (int or slice type).
        '''
        item2, single = convert_index_keys(self, item)
        super_delitem = super(IndexDict, self).__delitem__
        if single:
            return super_delitem(item2)
        else:
            return map(super_delitem, item2)


    def __contains__(self, item):
        'check if the dictionary contains one or multiple items (by key or index of key)'
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
    'check if index name is valid'
    if not isinstance(name, (str,unicode)):
        raise TypeError('Index name must be a str or unicode. '
            'Found type %s for %s' % (type(name), name))


def _get_unique_name(name, collection):
    '''
    generate a unique name by appending a sequence number to
    the original name so that it is not contained in the collection.
    `collection` has a __contains__ method (tuple, list, dict, etc.)
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
    'get length of value. if value has no len(), convert it to list first'
    try:
        Nvalue = len(value)
    except TypeError:
        # convert iterator/generator to list
        value = list(value)
        Nvalue = len(value)
    return Nvalue, value


def mid_parse_args(self, args, ingore_index2=False, allow_new=False):
    '''
    d[1]
    d[1,]
    # d[1, 'name']
    d[1, ['name', 'ip']]
    d[1, 'name':'ip']
    # d[1, ['name', 'ip'], 'other']

    d[:'192.1']
    d[:'192.1',]
    d['uid':2, 'name']
    d['uid':2, 'name', 'ip']
    d['uid':2, ('name', 'ip')]
    d['uid':2, ['name', 'ip']]
    d['uid':2, 'name':'ip']
    d['uid':2, 'uid':'ip']
    d['uid':2, 0:9]
    d['uid':2, 'uid':9]
    '''
    empty = len(self.indices) == 0
    if empty and not allow_new:
        raise KeyError('Item not found (dictionary is empty): %s' % (args,))

    names = self.indices.keys()
    N = len(names)

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

            if Nargs>1 and isinstance(args[1], (list,slice)):
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

        names = [] # list of names already passed in as arguments
        if index1 is not _default:
            if index1 is None:
                index1_last = True
                index1 = _default
            else:
                _check_index_name(index1)
                names.append(index1)
        if index2 is not _default:
            if isinstance(index2, (tuple, list)):
                map(_check_index_name, index2)
                names.extend(index2)
            elif isinstance(index2, slice):
                raise TypeError('Can not use slice as #2 argument when '
                    'dictionary is empty: %s' % index2)
            else:
                _check_index_name(index2)
                names.append(index2)

        # auto generate index names and avoid conficts with existing names
        if index1 is _default:
            if index1_last:
                if len(names) > 1:
                    name1 = 'index_%s' % (len(names) + 1)
                else:
                    name1 = 'index_2'
            else:
                name1 = 'index_1'
            index1 = _get_unique_name(name1, names)
            names.append(index1)

        if index2 is _default:
            name2 = 'index_1' if index1_last else 'index_2'
            index2 = _get_unique_name(name2, names)

        return index1, key, index2, index1_last

    # not empty:

    if index1 is _default:
        index1 = 0
    elif index1 is None:
        index1 = -1

    if index2 is _default:
        if not isinstance(index1, int):
            try:
                index1 = names.index(index1) # use index, int type
            except ValueError:
                raise KeyError('Index not found: %s' % (index1,))
        index2 = (index1 + 1) % N

    if isinstance(index1, int):
        index1 = names[index1]
    if isinstance(index2, int):
        index2 = names[index2]


    try:
        index_d = self.indices[index1]
    except KeyError:
        raise KeyError('Index not found: %s' % (index1,))

    try:
        item_d = index_d[key]
    except KeyError:
        if allow_new: # new key; item_d = None
            return index1, key, index2, None, None
        raise KeyError('Key not found in index "%s": %s' % (index1, key))

    try:
        value = item_d[index2]
    except KeyError:
        raise KeyError('Index not found: %s' % (index2,))
    return index1, key, index2, item_d, value


def _mid_init(self, *args, **kw):
    '''
    (items, **kw)
    (dict, **kw)
    (MultiIndexDict, **kw)

    (items, names, **kw)
    (dict, names, **kw)
    (MultiIndexDict, names **kw)
    '''

    items, names = [], None

    n_args = len(args)

    if n_args >= 1:
        items = args[0]

        if isinstance(items, Mapping): # copy from dict
            if isinstance(items, MultiIndexDict):
                names = items.indices.keys() # names may be overwritten by second arg
            items = items.items()
        else: # try to get data from items() or keys() method
            if hasattr(items, 'items'):
                try:
                    items = items.items()
                except TypeError: # items() may be not callalbe
                    if hasattr(items, 'keys'):
                        try:
                            items = [(k,items[k]) for k in items.keys()]
                        except TypeError:
                            pass

    if n_args >= 2:
        names = args[1]

    if n_args >= 3:
        raise TypeError('At most 2 positional arguments allowed (got %s)' % n_args)

    if items: # check item length
        n_index = len(items[0])
#            if n_index == 1:
#                raise ValueError('Length of item must be larger than 1')
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
                    'when keyword arguments are used' % n_index )
        items.extend(kw.items())

    if n_index > 0:
        if names is not None:
            if len(names) != n_index:
                raise ValueError('Length of names (%s) does not match '
                    'length of items (%s)' % (len(names), n_index))

    if names is None: # generate default names
        names = ['index_' + str(i) for i in range(n_index)]
    else:
        for name in names:
            if not isinstance(name, (str,unicode)):
                raise TypeError('Index name must be a str or unicode. '
                    'found type %s for %s' % (type(name), name))

    self.indices = d = IdxOrdDict() # the internal dict
    for index in names:
        if index in d:
            raise ValueError('Duplicate index name: %s' % (index,))
        d[index] = AttrOrdDict()

    # remove duplicate keys/items based on first index keys
    # for items with the same first index key, the last item will be used
    # duplicate keys in indices other than first index are not allowed
    items_d = OrderedDict()
    for item in items:
        if item:
            main_key = item[0]
            items_d[main_key] = item
    items = items_d.values()

    for item in items:
        item_d = IdxOrdDict(zip(names, item))

        for i, (index, value) in enumerate(item_d.items()):
            index_d = d[index]
            if value in index_d: # surely not in the main key/first index
                raise ValueError('Partially duplicate items not allowed: %s and %s'
                % (index_d[value].values(), item))
            index_d[value] = item_d


class MultiIndexDict(AttrOrdDict):
    '''
    Easily accessible dict with multiple indices.

    Example:

    d = MultiIndexDict(['uid', 'name', 'ip'],
                       [[1, 'jack', '192.1'],
                        [2, 'tony', '192.2']])

    * internal data structure: 3 levels of OrderedDict

    d -> OrderedDict([
        ('uid', OrderedDict([
            (1, OrderedDict([('uid', 1), ('name', 'jack'), ('ip', '192.1')])),
            (2, OrderedDict([('uid', 2), ('name', 'tony'), ('ip', '192.2')]))])),
        ('name', OrderedDict([
            ('jack', OrderedDict([('uid', 1), ('name', 'jack'), ('ip', '192.1')])),
            ('tony', OrderedDict([('uid', 2), ('name', 'tony'), ('ip', '192.2')]))])),
        ('ip', OrderedDict([
            ('192.1', OrderedDict([('uid', 1), ('name', 'jack'), ('ip', '192.1')])),
            ('192.2', OrderedDict([('uid', 2), ('name', 'tony'), ('ip', '192.2')]))]))
    ])


    * normal indexing of the internal dicts
    d['name']['jack']['uid'] -> 1
    d['name']['jack'][['uid','ip']] -> [1, '192.1'] # multiple keys and values
    d['name']['jack'] -> OrderedDict([
        ('uid', 1), ('name', 'jack'), ('ip', '192.1')])
    d['name'] -> OrderedDict([
        ('jack', OrderedDict([('uid', 1), ('name', 'jack'), ('ip', '192.1')])),
        ('tony', OrderedDict([('uid', 2), ('name', 'tony'), ('ip', '192.2')]))])


    * indexing via slice syntax and multiple indices:

    d[1,:] -> '192.1' # d[key_in_first_index,:] -> value_in_last_index
    d[:,'192.1'] -> 1 # d[:,key_in_last_index] -> value_in_first_index
    d['uid',1,'name'] -> 'jack' # d[index,key_in_index,index2] -> value_in_index2
    d['uid',1,['name','ip']] -> ['jack', '192.1'] # multiple keys and values


    * indexing via attribute chain (index, key_in_index, index2):

    d.uid[1].ip -> '192.1'
    d.ip['192.1'].uid -> 1
    d.name['jack'].ip -> '192.1'
    d.name.jack.ip -> '192.1' # access key 'jack' as attribute
    d.name.jack['uid', 'ip'] -> [1, '192.1']
    d.name.jack -> OrderedDict([('uid', 1), ('name', 'jack'), ('ip', '192.1')])
    d.name -> OrderedDict([
        ('jack', OrderedDict([('uid', 1), ('name', 'jack'), ('ip', '192.1')])),
        ('tony', OrderedDict([('uid', 2), ('name', 'tony'), ('ip', '192.2')]))])

    '''
    def __init__(self, *args, **kw):
#    def __init__(self, items=None, names=None):
        '''
        (items, **kw)
        (dict, **kw)
        (MultiIndexDict, **kw)

        (items, names, **kw)
        (dict, names, **kw)
        (MultiIndexDict, names **kw)


        init the dict with talbe-like data using flexible arguments.

        Example:

        +---------+---------+---------+
        |   uid   |  name   |   ip    |
        +=========+=========+=========+
        |    1    |  jack   |  192.1  |
        +---------+---------+---------+
        |    2    |  tony   |  192.2  |
        +---------+---------+---------+

        header_names = ['uid', 'name', 'ip']
        rows_of_data = [[1, 'jack', '192.1'],
                        [2, 'tony', '192.2']]

        data_with_header = [['uid', 'name', 'ip'],
                            [1, 'jack', '192.1'],
                            [2, 'tony', '192.2']]

        table_columns = [['uid', 1, 2],
                         ['name', 'jack', 'tony'],
                         ['ip', '192.1', '192.2']]

        # data_with_header == zip(*table_columns)

        # the following constructions have the same effect:

        d = MultiIndexDict(header_names, rows_of_data)

        d = MultiIndexDict(data_with_header)

        d = MultiIndexDict(indices=data_with_header)

        d = MultiIndexDict(items=data_with_header)

        d = MultiIndexDict(zip(*table_columns))


        # Construct from normal dict:

        normal_dict = {'jack':1, 'tony':2}
        mid = MultiIndexDict(['name', 'uid'], normal_dict.items())



        (a=1,b=2)
        ([[a,1], [b,2]])

        '''
        # MultiIndexDict.__mro__:
        # (MultiIndexDict, AccessibleOrderedDict, MultiDict, OrderedDict, dict, object)




        _mid_init(self, *args, **kw)

        # set normal attributes (instead of dict keys) before calling super's __init__()

        super(MultiIndexDict, self).__init__() # self is the internal dict


    def __getitem__(self, args):
        '''
        get values via slice syntax and multiple indices:

            d[key_in_first_index] -> value_in_last_index
            d[:key_in_last_index] -> value_in_first_index
            d[index:key_in_index,index2] -> value_in_index2

        index2 can be:
            key, key index, tuple/list/slice of keys or key indices

        '''

        return mid_parse_args(self, args)[-1]


    def __setitem__(self, args, value):
        '''
        set values via slice syntax and multiple indices

        int/slice syntax can only change value of existing key, not creating new keys
        '''
        empty = len(self.indices) == 0
        if empty:
            index1, key, index2, index1_last = mid_parse_args(self, args, allow_new=True)
            names = [index1]
            item = [key]
            try:
                _check_index_name(index2)
                names.append(index2)
                item.append(value)
            except TypeError:
                Nvalue, value = _get_value_len(value)
                if len(index2) != Nvalue:
                    raise ValueError('Number of keys (%s) based on argument %s does not match '
                        'number of values (%s)' % (len(index2), index2, Nvalue))
                names.extend(index2)
                item.extend(value)
            if index1_last:
                names = names[1:] + names[:1]
                item = item[1:] + item[:1]

            _mid_init(self, [item], names)
            return

        index1, key, index2, item_d, old_value = mid_parse_args(self, args, allow_new=True)
        index2_list, single = convert_index_keys(self.indices, index2)
        if single:
            index2_list = [index2_list]
            value = [value]
        else:
            Nvalue, value = _get_value_len(value)
            if len(index2_list) != Nvalue:
                raise ValueError('Number of keys (%s) based on argument %s does not match '
                    'number of values (%s)' % (len(index2_list), index2, Nvalue))

        if item_d is None: # new key
            self.indices[index1][key] = d =IdxOrdDict()
            d[index1] = key
            for k,v in zip(index2_list, value):
                d[k] = v
                self.indices[k][v] = d
        else: # existing key
            item_d[index2_list] = value
            if single:
                old_value = [old_value]
            for name, v_old, v_new in zip(index2_list, old_value, value):
                od_replace_key(self.indices[name], v_old, v_new)


    def __delitem__(self, args):
        '''
        delete keys/values via slice syntax and multiple indices
        '''
        index1, key, index2, item_d, value = mid_parse_args(self, args, ingore_index2=True)
        for name, v in item_d.items():
            del self.indices[name][v]


    ############################################
    # inherited methods from OrderedDict:
    # __ne__, __reduce__


    def __len__(self):
        'number of the items in an index'
        try:
            return len(self.indices.values()[0])
        except Exception:
            return 0

    def __eq__(self, other):
        """
        Test for equality with *other*.

        if `other` is a regular mapping/dict, compare only order-insensitive keys/values.
        if `other` is also a OrderedDict, also compare the order of keys.
        if `other` is also a MultiIndexDict, also compare the indices names.

        """
        if not isinstance(other, Mapping):
            return NotImplemented

        if isinstance(other, MultiIndexDict):
            return self.indices == other.indices

        if len(self.indices) != 2 or len(self) != len(other):
            return False

        # ignore indices names
        if isinstance(other, OrderedDict):
            d = OrderedDict(self.items()) # order-sensitive
        else:
            d = dict(self.items()) # order-insensitive

        return d == other

#    def __ne__(self, other):
#        return not self == other


    def __lt__(self, other):
        '''
        check if `self < other`

        if `other` is not a Mapping type, only compare the class name.

        if `other` is a Mapping type, compare in the following order:
            * length of items
            * length of indices (length of an individual item)
            * convert `self` to an OrderedDict or a dict (depends on the type of `other`)
              and compare it with `other`
            * indices names (only if `other` is a MultiIndexDict)

        '''
        if not isinstance(other, Mapping):
            return NotImplemented

        diff = len(self) - len(other)
        if diff < 0:
            return True
        elif diff > 0:
            return False
        # equal item length

        if isinstance(other, MultiIndexDict):
            len_other_indices = len(other.indices)
        else:
            len_other_indices = 2

        diff = len(self.indices) - len_other_indices
        if diff < 0:
            return True
        elif diff > 0:
            return False
        # equal indices length

        if isinstance(other, OrderedDict):
            d = OrderedDict(self.items()) # order-sensitive
        else:
            d = dict(self.items()) # order-insensitive

        if d < other:
            return True
        elif d > other:
            return False
        # equal items

        if isinstance(other, MultiIndexDict):
            # finally compare indices names
            return self.indices.keys() < other.indices.keys()

        return False # considered equal

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
        'MultiIndexDict(items, names)'
        call_key = id(self), _get_ident()
        if call_key in _repr_running:
            return '<%s(...)>' % self.__class__.__name__
        _repr_running[call_key] = 1
        try:
            try:
                if self.indices:
                    names = self.indices.keys()
                    return '%s(%s, %s)' % (self.__class__.__name__, self.items(), names)
            except AttributeError: # may not have attr `indices` yet
                pass
            return '%s()' % self.__class__.__name__
        finally:
            del _repr_running[call_key]


#    def __sizeof__(self):
#        'not very accurate.. '
#        try:
#            from pympler.asizeof import asizeof as getsizeof
#        except ImportError:
#            from sys import getsizeof
#
#        return getsizeof(self)


    def clear(self, clear_indices=False):
        'Remove all items. Indices names are removed if `clear_indices==True`.'
        if clear_indices:
            self.indices.clear()
        else:
            for index_d in self.indices.values():
                index_d.clear()


    @classmethod
    def fromkeys(cls, keys, value=None):
        '''
        Create a new dictionary with keys from `keys` and values set to value.

        fromkeys() is a class method that returns a new dictionary. value defaults to None.

        Length of `keys` must not exceed one because no duplicate values are allowed.
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
        Return the value for `key` if `key` is in the dictionary, else `default`.
        If `default` is not given, it defaults to None, so that this method never
        raises a `KeyError`.

        Support "multi-indexing" keys
        '''
        try:
            return self[key]
        except KeyError:
            return None


    def __contains__(self, key, index=0):
        '''
        Test for the presence of `key` in the dictionary.

        Support "multi-indexing" keys
        '''
        try:
            mid_parse_args(self, key, ingore_index2=True, allow_new=False)
            return True
        except KeyError:
            return False


    def has_key(self, key):
        '''
        Test for the presence of `key` in the dictionary. has_key() is deprecated
        in favor of `key in d`.

        Support "multi-indexing" keys
        '''
        return self.__contains__(key)



    ############################################

    # inherited methods from OrderedDict:
    # copy, pop, popitem, setdefault


    def __iter__(self, index=None):
        'Return an iterator through keys in the `index` (defaults to the first index)'
        if self.indices:
            if index is None:
                index = 0
            for k in self.indices[index]:
                yield k


    def __reversed__(self, index=None):
        'Return an reversed iterator through keys in the `index` (defaults to the first index)'
        if self.indices:
            if index is None:
                index = 0
            for k in reversed(self.indices[index]): # reverse OrderedDict
                yield k


    def iterkeys(self, index=None):
        'Return an iterator through keys in the `index` (defaults to the first index)'
        return self.__iter__(index)


    def keys(self, index=None):
        'Return a copy list of keys in the `index` (defaults to the first index)'
        return list(self.iterkeys(index))


    def itervalues(self, index=None):
        '''
        Return an iterator through values in the `index` (defaults to all indices
        except the first index).

        When `index is None`, yielded values depend on the length of indices (`N`):

            * if N == 0: return
            * if N <= 2: yield values in the last index
            * if N > 2: yield values in all indices except the first index
              (each value is a list of `N-1` elements)
        '''
        N = len(self.indices)

        if index is None:
            if N == 0:
                return
            elif N <= 2:
                index = -1
            else:
                index = slice(1,None)

        index, single = convert_index_keys(self.indices, index)

        if single:
            for k in self.indices[index]:
                yield k
            return

        if N == 0:
            if len(index) == 0:
                return
            else:
                raise KeyError('Index not found (dictionary is empty): %s' % (index,))

        for item_d in self.indices[0].values():
            yield item_d[index]


    def values(self, index=None):
        '''
        Return a copy list of values in the `index`.

        See the notes for `itervalues()`
        '''
        return list(self.itervalues(index))


    def iteritems(self, indices=None):
        'Return an iterator through items in the `indices` (defaults to all indices)'
        if indices is None:
            indices = self.indices.keys()
        return self.itervalues(indices)


    def items(self, indices=None):
        'Return a copy list of items in the `indices` (defaults to all indices)'
        return list(self.iteritems(indices))


    def update(self, *args, **kw):
        '''
        (items, **kw)
        (dict, **kw)
        (MultiIndexDict, **kw)

        '''
        if len(args) > 1:
            raise ValueError('Only one positional argument '
                '(items, dict, or MultiIndexDict) is allowed.')

        d = MultiIndexDict(*args, **kw)
        if not d.indices:
            return

        if not self.indices:
            self.indices = d.indices
            return

        names = self.indices.keys()

        if len(d.indices) != len(names):
            raise ValueError('Length of update items (%s) does not match '
                'length of original items (%s)' % (len(d.indices), len(names)))

        for item in d.items():
            item_d = IdxOrdDict(zip(names, item))

            for i, (index, value) in enumerate(item_d.items()):
                index_d = self.indices[index]
                if value in index_d:
                    if i == 0: # main key
                        del self[index:value] # del old item
                    else:
                        raise ValueError('Partially duplicate item: %s and %s'
                            % (index_d[value].values(), item_d.values()))
                index_d[value] = item_d


    def viewkeys(self, index=None):
        '''a set-like object providing a view on the keys in `index`
        (defaults to the first index)'''
        return MultiIndexKeysView(self, index)

    def viewvalues(self, index=None):
        '''a set-like object providing a view on the values in `index`
        (defaults to all indices except the first index)'''
        return MultiIndexValuesView(self, index)

    def viewitems(self, index=None):
        '''a set-like object providing a view on the items in `index`
        (defaults to all indices)'''
        return MultiIndexItemsView(self, index)


    ############################################


    def replace_index(self, *args):
        '''change the index name(s).

        * call with one argument:
            1. list of new indices names (to replace all old names)

        * call with two arguments:
            1. old index name(s) (or index/indices)
            2. new index name(s)
        '''
        old_indices = self.indices.keys()
        if len(args) == 1:
            new_indices = args[0]
        else:
            old_indices, new_indices = args
            old_indices, single = convert_index_keys(self.indices, old_indices)
            if single:
                old_indices, new_indices = [old_indices], [new_indices]

        if len(new_indices) != len(old_indices):
            raise ValueError('Length of update indices (%s) does not match '
                'existing indices (%s)' % (len(new_indices), len(old_indices)))
            map(_check_index_name, new_indices)

        for item_d in self.indices[0].values():
            od_replace_key(item_d, old_indices, new_indices, multi=True)

        od_replace_key(self.indices, old_indices, new_indices, multi=True)


    def add_index(self, items, name=None):
        'add an index of `name` with the list of `items`'
        if len(items) != len(self) and len(items) and self.indices:
            raise ValueError('Length of items in added index (%s) does not match '
                'length of existing items (%s)' % (len(items), len(self)))

        if name is None:
            name = 'index_' + str(len(self.indices))

        if self.indices:
            d = AttrOrdDict()
            for item, item_d in zip(items, self.indices[0].values()):
                item_d[name] = item
                d[name] = item_d
            self.indices[name] = d
        else:
            self.indices[name] = d = AttrOrdDict()
            for item in items:
                d[item] = IdxOrdDict([[name, item]])


    def remove_index(self, index):
        'remove an index. `index` can be the name (str) or index (int)'
        if not self.indices:
            raise KeyError('Index not found (dictionary is empty): %s' % (index,))
        for item_d in self.indices[0].values():
            del item_d[index]
        del self.indices[index]


############################################


class MultiIndexKeysView(KeysView):
    '''a set-like object providing a view on the keys in `index`
    (defaults to the first index)'''
    def __init__(self, mapping, index=0):
        if index not in mapping.indices:
            raise KeyError('Index not found: %s' % (index,))
        self.index = index
        super(MultiIndexKeysView, self).__init__(mapping)

    def __contains__(self, key):
        return key in self._mapping.indices[self.index]

    def __iter__(self):
        return self._mapping.iterkeys(self.index)


class MultiIndexValuesView(ValuesView):
    '''a set-like object providing a view on the values in `index`
    (defaults to all indices except the first index)'''
    def __init__(self, mapping, index=None):
        if index is not None and index not in mapping.indices:
            raise KeyError('Index not found: %s' % (index,))
        self.index = index
        super(MultiIndexValuesView, self).__init__(mapping)

    def __contains__(self, value):
        for v in iter(self):
            if value == v:
                return True
        return False

    def __iter__(self):
        return self._mapping.itervalues(self.index)


class MultiIndexItemsView(ItemsView):
    '''a set-like object providing a view on the items in `index`
    (defaults to all indices)'''
    def __init__(self, mapping, index=None):
        if index is not None and index not in mapping.indices:
            raise KeyError('Index not found: %s' % (index,))
        self.index = index
        super(MultiIndexItemsView, self).__init__(mapping)

    def __contains__(self, item):
        for v in iter(self):
            if item == v:
                return True
        return False

    def __iter__(self):
        return self._mapping.iteritems(self.index)






############################################


class G(object):
    def __getattr__(self, args):
        print 'G __getattr__', type(args), args

    def __setattr__(self, args, value):
        print 'G __setattr__', args, value

    def __getitem__(self, args):
        print 'G __getitem__', type(args), args

    def __setitem__(self, args, value):
        print 'G __setitem__', args, value

#g = G()

def test():
    m = IdxOrdDict(a=1,b=2)
    m['a'] = 10
    m['a','b'] = [10, 20]
    tuple_key = 'a','b','c'
    m[tuple_key] = [10, 20]
    m[tuple_key,] = 0,



    d = MultiIndexDict(
               [[1, 'jack', ('192.100', 81)],
                [2, 'tony', ('192.100', 82)]],
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
    d.replace_index(['a','b','c'])

    d = MultiIndexDict()
    # init like this:
    d[:'jack', 'uid'] = 1

    d['uid':2, 'name'] = 'jack'
    d['a'] = 1
    d.b = 20
    d[:1] = 'a'
    d[:3] = 'c'
    d.replace_index(['uid', 'name'])
    d.replace_index(['a', 'b'])
    d['uid':2] = 'jack'
    d['uid':2, 'name'] = 'jack'
    d.replace_index('uid', 'a')

    od = OrderedDict(a=1,b=2)


