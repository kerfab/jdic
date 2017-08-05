Jdic Documentation
******************

Overview:
"""""""""

In most projects, manipulating JSON documents requires to reinvent the wheel on a lot of small features. 

Jdic aims to avoid that: it is a ready-to-use library which aims to ease the manipulation of JSON-like documents, so that you can focus on your work instead of losing time in tedious document manipulations.


Features:
"""""""""

Here are the useful operations Jdic can do for you:

+ Easy to use - the API interface is minimal and is easy to learn and use.
+ Transparent JSON paths integration - for read and write operations, through an agnostic driver model. Currently MongoDB and Jsonpath-NG paths formats are natively supported.
+ Fast browsing of JSON documents - browse the entire data structure while getting useful values on each iteration: value, JSON path, parent, parent JSON path, depth, etc.
+ Find and Find-Match feature for quickly finding any value or subdocument matching MongoDB-like queries.
+ Merge features for fusioning dictionaries recursively, with up to 4 modes for handling conflicting arrays (replace, merge, new, append).
+ Diff & Patch features - so you can represent differences between two documents in compressed data (diff), and apply those differences to update documents (patch).
+ JSON Schema validation - if you need it, with auto-validation on each document change.
+ Consistent document checksuming - natively SHA-256, it allows to get a single checksum for the document, the checksum will always be the same on all systems.
+ Depth features - you can crawl your document at certain depths only.
+ Strict features - input data will be serialized to a strict JSON format.
+ Replacement for Python `enumerate()` which is agnostic of dicts or lists
+ Custom input serializer support - convert specific objects to the JSON data you want to.
+ Cache features with change detection to accelerate some of the API calls.


Examples:
"""""""""

.. code:: python

    from jdic import jdic

    o = { "a" : { "b" : { "c" : 1 } } } 
    j = jdic(o) # Accepts dicts and lists or Mapping, Sequence

    paths = [m.path for m in j.find(1)] # Find path for a value as-is
    >>> ["a.b.c"]

    paths = [m.parent_path for m in j.leaves()]  # Results include parents paths and more
    >>> ["a.b"] 

    paths = [m.depth for m in j.find({"c" : 1})] # find() target values can be objects
    >>> [2] 

    paths = [m.path for m in j.find_match({"c": {"$gt": 0}}) ] # match() and find_match() support mongo-like queries
    >>> ["a.b"]  

    paths = [m.path for m in j.find_match({  # Complex Mongo-like queries are permitted
        "$and" : [
            { "b.c": {"$exists" : True} },
            { "b.d": {"$exists" : False} }
        ]
    })]
    >>> ["a"]

    j.checksum()
    >>> ebd240a9ae435649514086d13c20d9963ec2844a1f866b313919c55a7c3f7ccb # Is consistent on all systems

    j["a"].checksum() # Sub-iterables have Jdic methods / all sub-iterables implement their own checksum()
    >>> 05a2013fbe17af7d58779ed96e0d74bd6fa3ce2726c1ebbd9f7dc33671b1c28e 

    j["a"] = None
    j.checksum()
    >>> 69d7d33051c5e05aa72f55a9a8e30a73da8d4afaa37127b9ea7ee29403aa9d3f # Change detection from child to parent

    j = jdic(o)
    p = { "a" : { "e" : { "f" : -1 } } }
    diff = j.diff(p)
    >>> [[["a"], {"e": {"f": -1}}]] # A diff stanza - on larger documents the diffs are smaller than documents

    j.patch(diff)
    j == p # Jdic objects can be transparently compared with dict or list objects 
    >>> True 

    q = { "a" : { "b" : { "d" : 2 } } }
    j.merge(q)
    >>> { "a": { "b": { "c": 1, "d": 2 } } } # Handles recursive merge

    j = jdic(o, schema = { 'type' : 'object' , 'properties' : { 'a' : { 'type' : 'object' } } }) # Correct Schema
    j['a'] = 3 # instant detection of schema violation (exception)
    >>> Traceback (most recent call last): ...

    # Agnostic enumerations with a revised enumerate() function
    from jdic import enumerate 
    y, z = [1,2,3], {'a':1, 'b':2}
    for k, v in enumerate(y): # Acts just as the original enumerate()
        y[k] = v
    for k, v in enumerate(z): # But it allows agnostic dict browsing the same way!
        z[k] = v

    j = jdic({'a' : [ {'b' : 1}, {'b' : 2}, {'b' : 3} ]}, driver = 'jsonpath_ng')
    j['a[*].b'] = 0 # Reassign the value to all locations at once!
    >>> { "a": [ {"b": 0}, {"b": 0}, {"b": 0} ] }

    del('a[*].b') # Also works with del()
    >>> { "a": [ {}, {}, {} ] }


Jdic object instanciation:
""""""""""""""""""""""""""

`jdic(obj, schema = None, serializer = None, driver = None):`
-------------------------------------------------------------

Instanciations of Jdic objects is made through the jdic() function which will decide for the type of Jdic object to instanciate and return.

+ `obj`: any list or dictionary. Sequence and Mapping equivalents will be casted to `dict` and `list`.

+ `schema`: optional, must be a JSON Schema in the form of a `dict`. If provided, all changes affecting the Jdic will be validated against the schema.

+ `serializer`: optional, your custom serialization function. It will be called to transform non-standard object types into standard JSON types. If not provided, exotic types are transformed to `str`. It is possible to use `settings.serialize_custom_function` instead, to globally specifiy a serializing function. The custom serializer function, if used, must return a JSON compliant data type: None, bool, str, int, float, list, dict.

+ `driver`: optional, a string representing the driver to use (`mongo` and `jsonpath_ng` are natively implemented). It is possible to use `settings.json_path_driver` instead, to globally specify a driver.


Jdic objects methods:
"""""""""""""""""""""

`browse(sort = False, depth = None, maxdepth = None):`
------------------------------------------------------

Recurse on all Jdic elements, yielding a `MatchResult` object on each iteration.

+ `sort`: if True all the results will be yielded with JSON paths in alphabetical order.
+ `depth`: an integer - only the results from objects at *depth* will be yielded.
+ `maxdepth` : an integer - will not recurse on documents whose depth is above `maxdepth`.

`checksum(algo='sha256'):`
--------------------------

Returns an ASCII checksum representing the content and data types of the object. Checksums are consistent from an execution to another and can be safely use for content change detection or objects comparisons. The checksum is cached and is only recalculated if changes occured.

+ `algo`: any algorithm supported by the `hashlib` Python library

`deepness():`
--------------

Returns an integer representing the deepness of the JSON structure from where `deepness()` is called. A document with no dict or list within it has a deepness of zero. The deepness is cached and is only recalculated if changes occured.

`depth():`
----------

Returns an integer representing the depth of the current document from the root of the Jdic object. The depth of the root document is 0.

`diff(obj)`:
------------

Returns an object (a diff *stanza*) representing the differences between the Jdic and `obj`. `diff()` is implemented by the `json_delta` Python library.

+ `obj`: any data

`enumerate(sort = False)`:
--------------------------

Agnostic and non-recursive enumeration of each entry in the current object. It yields a `(k, v)` tuple, where `k` is either an integer index when object is a list, and a string key when object is a dict. `v` is always the value. `enumerate()` is also available as a standalone function within the Jdic package.

+ `sort` : if True, sorts the dictionary keys alphabetically. Only sort dictionary keys, not lists.

`find(value, sort = False, limit = None, depth = None, maxdepth = None)`:
-------------------------------------------------------------------------

Searches a value within the entire Jdic. Searches are strict (`==`).

+ `value`: the value to search for - can be a simple type (int, str, etc.) or complex object (list, dict, Jdic, etc.)
+ `sort`: if True the search results will be sorted with JSON paths in alphabetical order.
+ `limit`: an integer - terminates the search when the number of results reaches `limit`.
+ `depth`: an integer - only the results from objects at *depth* will be yielded.
+ `maxdepth`: an integer - will not recurse on documents whose depth is above `maxdepth`.

`find_keys(keys, mode = "any", sort = False, limit = None, depth = None, maxdepth = None)`:
-------------------------------------------------------------------------------------------

Searches any sub-object containing `keys`. `keys` can be a single key or a list of keys. This function aims to facilitate finding sub-objects whose keys are known.

+ `keys`: a string or list of strings. The search will be case sensitive. Keys are for dicts and cannot be integer indexes of arrays. Keys cannot be JSON paths.
+ `mode`: `"any"` or `"all"` - if `"any"` then any object matching any of the provided keys will be yielded. If `"all"` then any object containing all the keys will be matched.
+ `sort`: if True the search results will be sorted with JSON paths in alphabetical order.
+ `limit`: an integer - terminates the search when the number of results reaches `limit`.
+ `depth`: an integer - only the results from objects at *depth* will be yielded.
+ `maxdepth`: an integer - will not recurse on documents whose depth is above `maxdepth`.

`find_match(query, sort = False, limit = None, depth = None, maxdepth = None)`:
-------------------------------------------------------------------------------

Finds all objects matching positive against `query`. Queries for `find_match()` are MongoDB-like queries, for both `mongo` and `jsonpath_ng` drivers. The underlying implementation is provided by the `mongoquery` Python library.

+ `query`: a MongoDB-like query. Please refer to the MongoDB documentation or the examples for information on queries structuration. Also review https://github.com/kapouille/mongoquery for more details on `mongoquery` and its known limitations.
+ `sort`: if True the search results will be sorted with JSON paths in alphabetical order.
+ `limit`: an integer - terminates the search when the number of results reaches `limit`.
+ `depth`: an integer - only the results from objects at *depth* will be yielded.
+ `maxdepth`: an integer - will not recurse on documents whose depth is above `maxdepth`.

`json(sort_keys = False, indent = 0, ensure_ascii = False)`:
------------------------------------------------------------

A helper to dump Jdic objects as serialized JSON strings.

+ `sort_keys`: all keys will be sorted alphabetically within their own dicts.
+ `indent`: number of spaces to add on new blocks.
+ `ensure_ascii`: for a pure ASCII output. Useless when the JSON objects do not contain binary info.

`leaves(sort = False, depth = None, maxdepth = None)`:
------------------------------------------------------

Will yield a `MatchResult` on each leaf encountered in the document. A leaf is a terminal value within the JSON documents. Basically all values are leaves, except dicts and lists.

+ `sort`: if True the search results will be sorted with JSON paths in alphabetical order.
+ `depth`: an integer - only the results from objects at *depth* will be yielded.
+ `maxdepth`: an integer - will not recurse on documents whose depth is above `maxdepth`.

`nb_leaves()`:
--------------

Returns an integer, the number of leaves contained in the Jdic object. This information is cached and is only recalculated if changes occured.

`match(query)`:
---------------

Returns `True` or `False` if the current Jdic object matches the Mongo-like query. Unlike `find_match()` it will not recurse into subdocuments. The current `match()` implementation is supported by the `mongoquery` Python library.

+ `query`: a Mongo-like query object

`merge(*args, arr_mode = "replace")`:
-------------------------------------

Will merge the current Jdic with one or multiple other objects (dicts or lists). It is not possible to merge a Jdic of type Mapping (dict) with a Sequence (list) or vice-versa. This limitation does not apply to sub-documents. Note that, unlike `patch()`, the method will change the state of the current object. If multiple args are provided then the next `arg` is merged on the result of the previous merge operation.

+ `args`: one or multiple objects of a similar type as the Jdic object itself.
+ `arr_mode`: determines how are handled the merging of conflicting arrays (arrays who are on the same JSON path). 4 modes are supported:
    + `"replace"`: arrays in Jdic are simply replaced.
    + `"append"`: arrays from `args` are appended to array in Jdic.
    + `"new"`: elements of arrays from `args` are appended, but only if they do not exist in the Jdic array.
    + `"merge"`: a recursive merge is processed on the elements of the same index. If there are more elements in `args` arrays then those are appended in the Jdic arrays.

`new()`:
--------

Returns an independant copy of the current Jdic, but inheriting its driver, schema and serializer. If the Jdic is a subdocument of another Jdic then it loses its parenthood information (detachment).

`parent(generation = 1)`:
-------------------------

Returns the Jdic parent of the current object. The root document has no parent (`None`).

+ `generation`: changes the generation of the parent returned. Eg. `2` will return the grand-parent. `0` always returns `None`. `None` is also returned when `generation` targets above the root Jdic document.

`patch(diff)`:
--------------

Applies a *diff stanza* as returned by `diff()` and returns a patched version of the Jdic object, without parenthood information. The original object is not modified. The underlying implementation is provided by the `json_delta` Python library.

+ `diff`: an object returned by `diff()`.

`path()`:
---------

Returns the full JSON path of the current Jdic object. Note that the JSON path format will depend of the current underlying driver in use. Eg: the root path for the `mongo` driver is an empty string (`""`) and `"$"` with the `jsonpath_ng` driver.

`raw()`:
--------

Returns a standalone non-Jdic object representing the JSON document. The result is a `list` or `dict`, depending of the type of the Jdic document (Sequence or Mapping). This function is useful for passing a Jdic in the form of pure Python basic types for compatibility purposes.

`validate(schema = None)`:
--------------------------

Validates the current Jdic with any JSON schema provided. If no argument is passed the Jdic is validated against its own schema, if it has any. Note that calling `validate()` without argument is useless if the Jdic is instantiated with a schema: in such case the Jdic object is constantly validated after a change. The schema validation features are supported by the `jsonschema` Python library.

+ `schema`: a JSON schema.


Related projects/libraries:
"""""""""""""""""""""""""""

json_delta: http://json-delta.readthedocs.io/en/latest/

jsonschema: https://github.com/Julian/jsonschema

mongoquery: https://github.com/kapouille/mongoquery

jsonpath_ng: https://github.com/h2non/jsonpath-ng


TODO:
"""""

+ Pip package
+ Readthedocs documentation
+ Documentation on drivers implementation
+ More tests
