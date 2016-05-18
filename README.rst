MIDict (Multi-Index Dict)
=========================

.. image:: https://img.shields.io/pypi/l/midict.svg
    :alt: License
    :target: ./LICENSE

.. image:: https://img.shields.io/pypi/v/midict.svg
    :target: https://pypi.python.org/pypi/midict
    :alt: PyPI Release

.. image:: https://img.shields.io/pypi/pyversions/midict.svg
    :target: https://pypi.python.org/pypi/midict
    :alt: Supported Python versions

.. .. image:: https://img.shields.io/pypi/dm/midict.svg
    :target: https://pypi.python.org/pypi/midict
    :alt: PyPI Downloads

.. image:: https://readthedocs.org/projects/midict/badge/?version=latest
    :target: https://midict.readthedocs.org/
    :alt: Documentation

.. image:: https://travis-ci.org/ShenggaoZhu/midict.svg?branch=master
    :target: https://travis-ci.org/ShenggaoZhu/midict
    :alt: Travis Build Status

.. image:: https://coveralls.io/repos/github/ShenggaoZhu/midict/badge.svg?branch=master
    :target: https://coveralls.io/github/ShenggaoZhu/midict?branch=master
    :alt: Test coverage


.. image:: https://api.codacy.com/project/badge/Grade/206345cabe8f44598c3632fb0a553eb1
    :target: https://www.codacy.com/app/zshgao/midict
    :alt: Code quality



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

The above table-like data set (with multiple columns/indices) can be represented using a ``MIDict``:

.. code-block:: python

    user = MIDict([['jack', 1, '192.1'], # list of items (rows of data)
                   ['tony', 2, '192.2']],
                  ['name', 'uid', 'ip']) # a list of index names

Access a key and get a value or a list of values (similar to a normal ``dict``):

.. code-block:: python

    user['jack'] == [1, '192.1']

Any index (column) can be used as the "keys" or "values" via the advanced
"multi-indexing" syntax ``d[index_key:key, index_value]``.
Both ``index_key`` and ``index_value`` can be a normal index name
or an ``int`` (the order the index), and ``index_value`` can also be a
``tuple``, ``list`` or ``slice`` object to specify multiple values, e.g.:

.. code-block:: python

    user['name':'jack', 'uid'] == 1
    user['ip':'192.1', 'name'] == 'jack'

    user['name':'jack', ('uid', 'ip')] == [1, '192.1']
    user[0:'jack', [1, 2]]             == [1, '192.1']
    user['name':'jack', 'uid':]        == [1, '192.1']

The "multi-indexing" syntax also has convenient shortcuts:

.. code-block:: python

    user['jack'] == [1, '192.1']
    user[:'192.1'] == ['jack', 1]
    user['jack', :] == ['jack', 1, '192.1']

A ``MIDict`` with 2 indices can be used as a bidirectional/inverse dict:

.. code-block:: python

    mi_dict = MIDict(jack=1, tony=2)

    mi_dict['jack'] == 1 # forward indexing: d[key] -> value
    mi_dict[:1]     == 'jack' # backward/inverse indexing: d[:value] -> key



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

Testing
^^^^^^^

``python tests/tests.py``

Tested with both Python 2.7 and Python 3,3, 3.4, 3.5.
