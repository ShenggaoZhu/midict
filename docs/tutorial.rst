===============
MIDict Tutorial
===============

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
for dict keys). Here, a "super dict" is wanted to represent this table
which allows any index (column) to be used as the "keys" to index the table.
Such a "super dict" is called a multi-index dictionary (MIDict).

A multi-index dictionary ``user`` can be constructed with two arguments:
a list of items (rows of data), and a list of index names::

    user = MIDict([['jack', 1, '192.1'],
                   ['tony', 2, '192.2']],
                  ['name', 'uid', 'ip'])

Index names are for easy human understanding and indexing, and thus
must be a string. The index names and items are ordered
in the dictionary. Compatible with a normal ``dict``, the first index (column)
is the primary index to lookup/index a key, while the rest index or indices
contain the corresponding key's value or list of values::

    user['jack'] -> [1, '192.1']

To use any index (column) as the "keys", and other one or more
indices as the "values", just specify the indices via the advanced
"multi-indexing" syntax ``d[index_key:key, index_value]``, e.g.::

    user['name':'jack', 'uid'] -> 1
    user['ip':'192.1', 'name'] -> 'jack'

Here, ``index_key`` is the single column used as the "keys", and ``key`` is
an element in ``index_key`` to locate the row of record (e.g.,
``['jack', 1, '192.1']``) in the table. ``index_value`` can be one or more columns
to specify the value(s) from the row of record.


Multi-value indexing syntax
---------------------------

For a multi-column data set, it's useful to be able to access multiple
values/columns at the same time.

In the indexing syntax ``d[index_key:key, index_value]``, both ``index_key``
and ``index_value`` can be a normal index name
or an ``int`` (the order the index), and ``index_value`` can also be a
``tuple``, ``list`` or ``slice`` object to specify multiple values/columns,
with the following meanings:

========== ========================================= ====================
    type                    meaning                  corresponding values
========== ========================================= ====================
int        the index of a key in d.keys()            the value of the key
---------- ----------------------------------------- --------------------
tuple/list multiple keys or indices of keys          list of values
---------- ----------------------------------------- --------------------
slice      a range of keys (key_start:key_stop:step) list of values
========== ========================================= ====================

The elements in the tuple/list or ``key_start``/``key_stop`` in the slice
syntax can be a normal index name or an ``int``.

See :class:`midict.IndexDict` for more details.

Using the above ``user`` example::

    user['name':'jack', ['uid', 'ip']] -> [1, '192.1']
    <==> user['name':'jack', [1, 2]]
    <==> user['name':'jack', 'uid':]
    <==> user[0:'jack', 1:]


Convenient indexing shortcuts
-----------------------------

Full syntax: ``d[index_key:key, index_value]``

Short syntax::

    d[key] <==> d[first_index:key, all_indice_except_first_index]
    d[:key] <==> d[None:key] <==> d[last_index:key, all_indice_except_last_index]
    d[key, index_value] <==> d[first_index:key, index_value] # only when ``index_value`` is a list or slice object
    d[index_key:key, index_value_1, index_value_2, ...] <==> d[index_key:key, (index_value_1, index_value_2, ...)]

Examples::

    user['jack'] -> [1, '192.1']
    user[:'192.1'] -> ['jack', 1]
    user['jack', :] -> ['jack', 1, '192.1']
    user['jack', ['uid', 'ip']] -> [1, '192.1']
    user[0:'jack', 'uid', 'ip'] -> [1, '192.1']


Bidirectional/inverse dict
--------------------------

With the advanced "multi-indexing" syntax, a MIDict with 2 indices
can be used as a normal dict, as well as a convenient
**bidirectional dict** to index using either a key or a value::

    mi_dict = MIDict(jack=1, tony=2)

* Forward indexing like a normal dict (``d[key] -> value``)::

      mi_dict['jack'] -> 1
      <==> mi_dict[0:'jack', 1]

* Backward/inverse indexing using the slice syntax (``d[:value] -> key``)::

      mi_dict[:1] -> 'jack'
      <==> mi_dict[-1:1, 0]


Compatible with normal dict in Python 2 & 3
-------------------------------------------

A ``MIDict`` with 2 indices is fully compatible with the normal dict
or OrderedDict, and can be used as a drop-in replacement of the latter::

    normal_dict = dict(jack=1, tony=2)
    mi_dict = MIDict(jack=1, tony=2)

The following equality checks all return ``True``::

    mi_dict == normal_dict
    normal_dict['jack'] == mi_dict['jack'] == 1
    normal_dict.keys() == mi_dict.keys() == ['tony', 'jack']
    normal_dict.values() == mi_dict.values() == [2, 1]

Conversion between ``MIDict`` and ``dict`` is supported in both directions::

    mi_dict == MIDict(normal_dict) # True
    normal_dict == dict(mi_dict) # True
    normal_dict == mi_dict.todict() # True

The ``MIDict`` API also matches the ``dict`` API in Python 2 & 3. For example,
in Python 2, ``MIDict`` has methods ``keys()``, ``values()`` and ``items()``
that return lists. In Python 3, those methods return dictionary views, just like ``dict``.

Accessing keys via attributes
-----------------------------

Use the attribute syntax to access a key in MIDict if it is a valid
Python identifier (``d.key <==> d['key']``)::

    mi_dict.jack <==> mi_dict['jack']

This feature is supported by :class:`midict.AttrDict`.

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
MIDict provides special methods (``d.reorder_indices()``, ``d.rename_index()``,
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

When setting an item using syntax ``d[index_key:key, index_value] = value2``,
if ``key`` already exists in ``index_key``, the item of ``key`` will be updated
according to ``index_value`` and ``value2`` (similar to updating the value of a key in
a normal ``dict``). However, if any value of ``value2``
already exists in ``index_value``, a ``ValueExistsError`` will be raised.

When constructing a MIDict or updating it with ``d.update()``,
duplicate keys/values are handled in the same way as above with
the first index treated as ``index_key`` and the rest indices treated as ``index_value``::

    d = MIDict(jack=1, tony=2)

    d['jack'] = 10 # replace value of key 'jack'
    d['tom'] = 3 # add new key/value
    d['jack'] = 2 # raise ValueExistsError
    d['alice'] = 2 # raise ValueExistsError
    d[:2] = 'jack' # raise ValueExistsError
    d['jack', :] = ['tony', 22] # raise ValueExistsError
    d['jack', :] = ['jack2', 11] # replace key 'jack' to a new key 'jack2' and value to 11

    d.update([['alice', 2]]) # raise ValueExistsError
    d.update(alice=2) # raise ValueExistsError
    d.update(alice=4) # add new key/value

    MIDict([['jack',1]], jack=2) # {'jack': 2}
    MIDict([['jack',1], ['jack',2]]) # {'jack': 2}
    MIDict([['jack',1], ['tony',1]]) # raise ValueExistsError
    MIDict([['jack',1]], tony=1) # raise ValueExistsError


Internal data struture
----------------------

Essentially ``MIDict`` is a ``Mapping`` type, and it stores the data in the form of
``{key: value}`` for 2 indices (identical to a normal ``dict``) or
``{key: list_of_values}`` for more than 2 indices.

Additionally, MIDict uses a special attribute ``d.indices`` to store
the indices, which is an ``IdxOrdDict`` instance with the index names as keys
(the value of the first index is the ``MIDict`` instance itself, and the value of
each other index is an ``AttrOrdDict`` instance which maps each element in that index
to its corresponding element in the first index)::

    d = MIDict([['jack', 1], ['tony', 2]], ['name', 'uid'])

    d.indices ->

        IdxOrdDict([
            ('name', MIDict([('jack', 1), ('tony', 2)], ['name', 'uid'])),
            ('uid', AttrOrdDict([(1, 'jack'), (2, 'tony')])),
        ])

Thus, ``d.indices`` also presents an interface to access the indices and items.

For example, access index names::

    'name' in d.indices -> True
    list(d.indices) -> ['name', 'uid']
    d.indices.keys() -> ['name', 'uid']

Access items in an index::

    'jack' in d.indices['name'] -> True
    1 in d.indices['uid'] -> True
    list(d.indices['name']) -> ['jack', 'tony']
    list(d.indices['uid']) -> [1, 2]
    d.indices['name'].keys() -> ['jack', 'tony']
    d.indices['uid'].keys() -> [1, 2]

``d.indices`` also supports the attribute syntax::

    d.indices.name -> MIDict([('jack', 1), ('tony', 2)], ['name', 'uid'])
    d.indices.uid -> AttrOrdDict([(1, 'jack'), (2, 'tony')])

However, the keys/values in ``d.indices`` should not be directly changed,
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
    user[0:3, ['name','ip']] = ['tom', '192.3'] # set a new item explictly
    <==> user[0:3] = ['tom', '192.3'] # set a new item implicitly
    # result:
    # user -> MIDict([[1, 'jack', '192.1'],
                      [2, 'tony', '192.2'],
                      [3, 'tom', '192.3']],
                     ['uid', 'name', 'ip'])




More classes and functions
--------------------------
Check :doc:`midict` for more classes and functions,
such as :class:`midict.FrozenMIDict`, :class:`midict.AttrDict`, :class:`midict.IndexDict`,
:class:`midict.MIDictView`, etc.


