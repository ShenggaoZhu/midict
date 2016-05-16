MIDict (Multi-Index Dict)
=========================

``MIDict`` is an ordered "dictionary" with multiple indices
where any index can serve as "keys" or "values",
capable of assessing multiple values via its powerful indexing syntax,
and suitable as a bidirectional/inverse dict (a drop-in replacement
for dict/OrderedDict in Python 2 & 3).


Features
--------

* Multiple indices
* Multi-value indexing syntax
* Convenient indexing shortcuts
* Bidirectional/inverse dict
* Compatible with normal dict in Python 2 & 3
* Accessing keys via attributes
* Extended methods for multi-indices
* Additional APIs to handle indices
* Duplicate keys/values handling


Quickstart
----------

+---------+---------+---------+
|  name   |   uid   |   ip    |
+=========+=========+=========+
|  jack   |    1    |  192.1  |
+---------+---------+---------+
|  tony   |    2    |  192.2  |
+---------+---------+---------+

The above table-like data set (with multiple columns/indices) can be represented using a ``MIDict``::

    user = MIDict([['jack', 1, '192.1'], # list of items (rows of data)
                   ['tony', 2, '192.2']],
                  ['name', 'uid', 'ip']) # a list of index names

Access a key and get a value or a list of values (similar to a normal ``dict``)::

    user['jack'] -> [1, '192.1']

Any index (column) can be used as the "keys" or "values" via the advanced
"multi-indexing" syntax ``d[index_key:key, index_value]``.
Both ``index_key`` and ``index_value`` can be a normal index name
or an ``int`` (the order the index), and ``index_value`` can also be a
``tuple``, ``list`` or ``slice`` object to specify multiple values, e.g.::

    user['name':'jack', 'uid'] -> 1
    user['ip':'192.1', 'name'] -> 'jack'

    user['name':'jack', ('uid', 'ip')] -> [1, '192.1']
    user[0:'jack', [1, 2]] -> [1, '192.1']
    user['name':'jack', 'uid':] -> [1, '192.1']

The "multi-indexing" syntax also has convenient shortcuts::

    user['jack'] -> [1, '192.1']
    user[:'192.1'] -> ['jack', 1]
    user['jack', :] -> ['jack', 1, '192.1']

A ``MIDict`` with 2 indices can be used as a bidirectional/inverse dict::

    mi_dict = MIDict(jack=1, tony=2)
    mi_dict['jack'] -> 1 # forward indexing: d[key] -> value
    mi_dict[:1] -> 'jack' # backward/inverse indexing: d[:value] -> key



Documentation
-------------

See https://midict.readthedocs.io


Installation
------------

``pip install midict``


Development
-----------

Source code:  https://github.com/ShenggaoZhu/midict

Report issues: https://github.com/ShenggaoZhu/midict/issues/new

**Test**

``python tests/tests.py``

Tested with both Python 2.7 and Python 3.5.
