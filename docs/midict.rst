.. _midict-API:

midict package API
==================

.. currentmodule:: midict

midict.AttrDict
---------------

.. autoclass:: AttrDict
.. autoclass:: AttrOrdDict


midict.IndexDict
----------------

.. autoclass:: IndexDict
.. autoclass:: IdxOrdDict


midict.MIMapping
----------------

.. autoclass:: MIMapping


midict.MIDict
-------------

.. autoclass:: MIDict


midict.FrozenMIDict
-------------------

.. autoclass:: FrozenMIDict


Exceptions
----------

.. autoexception:: MIMappingError
.. autoexception:: ValueExistsError


Dict views
----------

.. autoclass:: MIKeysView
.. autoclass:: MIValuesView
.. autoclass:: MIItemsView
.. autoclass:: MIDictView


Auxiliary functions
-------------------

.. automodule:: midict
    :exclude-members: OrderedDict, AttrDict, AttrOrdDict, IndexDict, IdxOrdDict,
        MIMapping, MIDict, FrozenMIDict, MIMappingError, ValueExistsError,
        MIKeysView, MIValuesView, MIItemsView, MIDictView

    .. autofunction:: _MI_init
    .. autofunction:: _MI_setitem
