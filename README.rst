=======================
MultiIndexDict (midict)
=======================

A dictionary that has multiple indices and can index multiple items.



Consider a table-like data set (e.g., a user table):

+---------+---------+---------+
|  name   |   uid   |   ip    |
+=========+=========+=========+
|  jack   |    1    |  192.1  |
+---------+---------+---------+
|  tony   |    2    |  192.2  |
+---------+---------+---------+

In each column, elements are unique and hashable (suitable for dict keys).

A multi-index `user` dictionary can be constructed like this::

    user = MultiIndexDict([['jack', 1, '192.1'],
                           ['tony', 2, '192.2']],
                          ['name', 'uid', 'ip'])

The indices and items are ordered in the dictionary. Like a normal dict,
the first index (column) is the main "keys" for indexing, while the rest
index or indices are the "values"::

    user['jack'] -> [1, '192.1']


More powerful functions are supported by MultiIndexDict via the advanced
indexing syntax:

1. To use any index (column) as the "keys", and other one or more
   indices as the "values", just specify the indices as follows::

       user[index1:key, index2]
       # e.g.:
       user['name':'jack', 'uid'] -> 1

   Here, index `index1` is used as the "keys", and `key` is an element
   in `index1` to locate the row of record in the table. `index2` can
   be one or more indices to get the value(s) from the row of record.

2. Index multiple items at the same time::

       user['name':'jack', ['uid','ip']] -> [1, '192.1']
       user['name':'jack', 1:] -> [1, '192.1']

3. Index via various shortcuts::

       user['jack'] -> [1, '192.1']
       user[:'192.1'] -> ['jack', 1]
       user['jack', :] -> ['jack', 1, '192.1']

4. Use attribute syntax to access a key if it is a valid Python
   identifier::

       user.jack -> [1, '192.1']


A MultiIndexDict with 2 indices is fully compatible with the normal dict
or OrderedDict::

    normal_dict = {'jack':1, 'tony':2}
    user_dict = MultiIndexDict(normal_dict, ['name', 'uid'])

    user_dict -> MultiIndexDict([['tony', 2], ['jack', 1]], ['name', 'uid'])
    user_dict == normal_dict -> True

With the advanced indexing syntax, it can be used as a convenient
**bidirectional dict**::

    user_dict['jack'] -> 1 # forward indexing
    user_dict[:1] -> 'jack' # backward indexing


More examples of advanced indexing:

* Example of two indices (compatible with normal dict)::

    color = MultiIndexDict([['red', '#FF0000'], ['green', '#00FF00']],
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


    # setting item using different indices/keys:

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
    # color -> MultiIndexDict([['red', '#FF0000'],
                               ['green', '#00FF00'],
                               ['blue', '#0000FF']],
                              ['name', 'hex'])


* Example of three indices::

    user = MultiIndexDict([[1, 'jack', '192.1'],
                           [2, 'tony', '192.2']],
                          ['uid', 'name', 'ip'])

    user[1]                     -> 'jack'
    user['name':'jack']         -> '192.1'
    user['uid':1, 'ip']         -> '192.1'
    user[1, ['name','ip']]      -> ['jack', '192.1']
    user[1, ['name',-1]]        -> ['jack', '192.1']
    user[1, [1,1,0,0,2,2]]      -> ['jack', 'jack', 1, 1, '192.1', '192.1']
    user[1, :]                  -> [1, 'jack', '192.1']
    user[1, 'name':]            -> ['jack', '192.1']
    user[1, 0:-1]               -> [1, 'jack']
    user[1, 'name':-1]          -> ['jack']
    user['uid':1, 'name','ip']  -> ['jack', '192.1']
    user[0:3, ['name','ip']] = ['tom', '192.3']
    # result:
    # user -> MultiIndexDict([[1, 'jack', '192.1'],
                              [2, 'tony', '192.2'],
                              [3, 'tom', '192.3']],
                             ['uid', 'name', 'ip'])


* Internal data structure `d.indices`: 3 levels of ordered dicts::

    color.indices ->

    IdxOrdDict([('name',
                 AttrOrdDict([('red',
                               IdxOrdDict([('name', 'red'), ('hex', '#FF0000')])),
                              ('green',
                               IdxOrdDict([('name', 'green'),
                                           ('hex', '#00FF00')]))])),
                ('hex',
                 AttrOrdDict([('#FF0000',
                               IdxOrdDict([('name', 'red'), ('hex', '#FF0000')])),
                              ('#00FF00',
                               IdxOrdDict([('name', 'green'),
                                           ('hex', '#00FF00')]))]))])



    color.indices.name.red.hex # -> '#FF0000'
    <==> color.indices['name']['red']['hex']




More docs are inside the code. Go ahead the check it!
