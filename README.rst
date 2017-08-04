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

    paths = [m.parent_path for m in j.find(1)]  # Results include parents paths and more
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
    >>> 'ebd240a9ae435649514086d13c20d9963ec2844a1f866b313919c55a7c3f7ccb' # Is consistent on all systems

    j["a"].checksum() # Sub-iterables have Jdic methods
    >>> '05a2013fbe17af7d58779ed96e0d74bd6fa3ce2726c1ebbd9f7dc33671b1c28e'

    j["a"] = None
    j.checksum()
    >>> '69d7d33051c5e05aa72f55a9a8e30a73da8d4afaa37127b9ea7ee29403aa9d3f' # Change detection from child to parent

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
    j['a'] = 3 # violates schema - instant detection (exception)
    >>> Traceback (most recent call last): ...
