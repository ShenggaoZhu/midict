MIDict (Multi-Index Dict)
=========================

``MIDict`` is an ordered "dictionary" with multiple indices
where any index can serve as "keys" or "values",
capable of assessing multiple values via its powerful indexing syntax,
and suitable as a bidirectional/inverse dict (a drop-in replacement
for dict/OrderedDict in Python 2 & 3).


Quick example
-------------

Consider a table-like data set (e.g., a user table):

+---------+---------+---------+
|  name   |   uid   |   ip    |
+=========+=========+=========+
|  jack   |    1    |  192.1  |
+---------+---------+---------+
|  tony   |    2    |  192.2  |
+---------+---------+---------+

A multi-index dictionary ``user`` can be constructed with two arguments:
a list of items (rows of data), and a list of index names::

    user = MIDict([['jack', 1, '192.1'],
                   ['tony', 2, '192.2']],
                  ['name', 'uid', 'ip'])

Access a key and get multi-values::

    user['jack'] -> [1, '192.1']

Any index (column) can be used as the "keys" or "values" via the advanced
"multi-indexing" syntax ``d[index1:key, index2]`` where
both ``index1`` and ``index2`` support flexible indexing using a normal key
or an ``int``, and ``index2`` can also be a ``tuple``, ``list`` or ``slice`` object,
e.g.::

    user['name':'jack', 'uid'] -> 1
    user['ip':'192.1', 'name'] -> 'jack'

    user['name':'jack', ['uid', 'ip']] -> [1, '192.1']
    user[0:'jack', [1, 2]] -> [1, '192.1']
    user['name':'jack', 'uid':] -> [1, '192.1']

The "multi-indexing" syntax also has convenient shortcuts::

    user['jack'] -> [1, '192.1']
    user[:'192.1'] -> ['jack', 1]
    user['jack', :] -> ['jack', 1, '192.1']



Installation
------------

``pip install midict``

Git Repo:  https://github.com/ShenggaoZhu/midict



Table of Contents:
==================
.. toctree::
   :maxdepth: 2

   tutorial
   midict



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

