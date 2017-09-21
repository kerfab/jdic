# -*- coding: utf-8 -*-
from jdic import settings, jdic, JdicSequence
from copy import copy, deepcopy

settings.json_path_driver = "mongo"

def new(asdict = False, schema = None, serializer = None, driver = None):
    o = {
        1 : 'éàè',
        2 : Exception('TestSerialize', 'Just a test'),
        3 : { None : 0 },
        None : { "None" },
        'a' : None,
        'b' : 0.1,
        'c' : 5.0,
        'd' : { 'da' : 'db' },
        'e' : { 'ea' : { 'eb' : 'ec' } },
        'f' : { 'fa' : { 'fab' : 'fac' },
                'fb' : { 'fbc' : 'fbd' } },
        'g' : { 'a' : { 'b' : [1,2,3] },
                'b' : { 'c' : [4,5,6] } },
        'h' : { 'a' : { 'b' : [[1,2],[3,4],[5,6]] },
                'b' : { 'c' : [[None, "Ok"], [-1, 1.0], [{'d' : 'e'}]] } },
        'i' : [1,2,3],
        'j' : [{'a':1}, {'a':2}, {'b':2}, {'c':3}],
        'k' : [[{'a':1}, {'b':2}], [{'c':3}]],
        'l' : [[[{'a':1}, {'b':2}]], [[{'c':3}, None]]],
        'm' : { 'a' : [ { 'b' : [ { 'c' : 3 }, None ] } ] }
    }
    if asdict:
        return o
    return jdic(o, schema = schema, serializer = serializer, driver = driver)

expected_match_attributes = [
    'parent',
    'parent_path',
    'value',
    'path',
    'key',
    'depth'
]

def log(*args):
    print("\n-----------------------------------")
    print(args)
    print("------------------------------------\n\n")

def test_browse_match_attributes():
    for match in new().browse():
        for a in expected_match_attributes:
            getattr(match, a)

def test_checksum():
    o = new()
    c = o.checksum()
    backup = copy(o['m.a.0.b'])
    o['m.a.0.b'] = None
    assert c != o.checksum()
    o['m.a.0.b'] = backup
    assert c == o.checksum()
    del(o['m.a.0.b'])
    assert c != o.checksum()
    o['m.a.0.b'] = backup
    assert c == o.checksum()
    o['m.a.0.b'].append(666)
    assert c != o.checksum()
    o['m.a.0.b'] = backup
    assert c == o.checksum()
    o['m.a.0'].update({'b':4})
    assert c != o.checksum()
    o['m.a.0.b'] = deepcopy(backup)
    assert c == o.checksum()

def test_custom_serializer():
    def myserializer(obj):
        if isinstance(obj, Exception):
            return "Python Exception"
        return obj
    o = new(serializer = myserializer)
    assert o['2'] == "Python Exception"
    o = new()
    assert o['2'] != "Python Exception"
    settings.serialize_custom_function = myserializer
    o = new()
    assert o['2'] == "Python Exception"
    settings.serialize_custom_function = None

def test_copy_deepcopy():
    o = new()
    assert o == deepcopy(o)
    assert o == copy(o)
    assert type(copy(o)['2']).__name__ == 'str'
    assert o['d'] == copy(o['d'])
    assert o['d'] == deepcopy(o['d'])
    j = copy(o['d'])
    j.update({'da':'dc'})
    assert o['d'] == {'da':'db'}
    o['d'] = j
    assert o['d'] == {'da':'dc'}

def test_depth_deepness():
    o = jdic({'a':{'b':{'c':{'d':1}}}, 'e':True})
    assert o['a.b.c'].depth() == 3
    assert o.deepness() == 3
    assert [m.value for m in o.browse(depth = 3)] == [1]
    assert [m.value for m in o.leaves(depth = 3)] == [1]
    assert [m.value for m in o.leaves(maxdepth = 2)] == [True]
    assert [m.value for m in o.leaves(maxdepth = 3, sort = True)] == [1, True]
    assert o.depth() == 0
    o = jdic({})
    assert o.deepness() == 0

def test_diff_patch():
    o = new()
    p = new()
    o['l.0.0'].append(7777)
    assert o != p
    d = o.diff(p)
    assert d == [[['l', 0, 0, 2]]]
    o.patch(d)
    assert o != p
    o = o.patch(d)
    assert o == p
    o['l.0.0'].append(7777)
    assert o != p
    d = p.diff(o)
    assert d == [[['l', 0, 0, 2], 7777]]
    p = p.patch(d)
    assert o['l.0.0'] == p['l.0.0']
    assert o == p
    p = [1,2,3]
    o = jdic({'a':1})
    o = o.patch(o.diff(p))
    assert isinstance(o, JdicSequence)
    assert o == p  
    p = None
    assert o.patch(o.diff(p)) == None

def test_enumerate():
    from jdic import enumerate
    a = [1,2,3]
    b = {'a' : 1, 'b' : 2}
    for k, v in enumerate(a):
        a[k] = v
    for k, v in enumerate(b):
        b[k] = v

def test_exception_serialized():
    o = new()
    assert type(o['2']).__name__ == 'str'

def test_float_serialized():
    o = new()
    assert type(o['c']).__name__ == 'int'

def test_json_schema():
    schema = { 
        "type" : "object",
        "properties" : { 
            "a" : { 
                "type" : "null"
            } 
        }
    }
    o = new(schema = schema)
    o.validate()
    exception = False
    try:
        o['a'] = 3
    except:
        exception = True
    assert exception
    schema = {
        "type" : "object",
        "properties" : {
            "a" : {
                "type" : "object"
            }
        }
    }
    exception = False
    try:
        o.validate(schema)
    except:
        exception = True
    assert exception
    exception = False
    try:
        o.new(schema = schema)
    except:
        exception = True
    assert exception

def test_parent_serialized():
    o = new()
    assert o['m.a.0.b'].parent().path() == 'm.a.0' and o['m.a.0.b'].parent() == o['m.a.0']
    assert o['m.a.0.b'].parent(3) == o['m']
    assert o['m.a.0.b'].parent(10) == None

def test_set_value():
    o = new()
    o['test'] = None
    assert o._obj['test'] == None

def test_sort():
    paths = [r.path for r in new().browse(sort = True)]
    p = deepcopy(paths)
    p.sort()
    assert p == paths

def test_attr_proxy():
    o = new()
    o['d'].update({ 'da' : 'dc' })
    assert o['d'] == { 'da' : 'dc' }

def test_nb_leaves():
    o = jdic({
        'a':1,
        'b': {'c':2},
        'c': [{'d':3}, 4],
        'f': [[{'g':5},6],7]
    })
    assert o.nb_leaves() == 7
    del(o['a'])
    assert o.nb_leaves() == 6
    o['f']['0.0'].update({'h':8})
    assert o.nb_leaves() == 7
    assert o == {
        'b': {'c':2},
        'c': [{'d':3}, 4],
        'f': [[{'g':5, 'h':8},6],7]
    }

def test_leaves():
    o = jdic({
        'a':1,
        'b': {'c':2},
        'c': [{'d':3}, 4],
        'f': [[{'g':5},6],7]
    })
    assert [r.path for r in o.leaves(sort = True)] == ['a', 'b.c', 'c.0.d', 'c.1', 'f.0.0.g', 'f.0.1', 'f.1']
    assert [r.key for r in o.leaves(sort = True)] == ['a', 'c', 'd', 1, 'g', 1, 1]
    parent_paths = [r.parent_path for r in o.leaves(sort = True)]
    assert parent_paths == ['', 'b', 'c.0', 'c', 'f.0.0', 'f.0', 'f']
    parents = [r.parent for r in o.leaves(sort = True)]
    assert parents[1] == {'c':2}
    assert parents[0] == o
    depths = [r.depth for r in o.leaves(sort = True)]
    assert depths == [0, 1, 2, 1, 3, 2, 1]
    values = [r.value for r in o.leaves(sort = True)]
    assert values == [1, 2, 3, 4, 5, 6, 7]
    
def test_find():
    o = new()
    assert len([r for r in o.find({'c':3})]) == 4
    assert len([r for r in o.find({'c':3}, limit = 1)]) == 1

def test_find_keys():
    o = new()
    assert [m.path for m in o.find_keys('fab')] == ['f.fa']
    assert [m.path for m in o.find_keys(['fab', 'fbc'], sort = True)] == ['f.fa', 'f.fb']
    assert [m.path for m in o.find_keys(['fa', 'fb'], mode = "all")] == ['f']
    assert [m.path for m in o.find_keys('none')] == []

def test_merge():
    o = jdic({ 'a' : 1, 'b' : 2})
    o.merge({'a':2,'b':3})
    assert o == {'a':2, 'b':3}
    o.merge({'a':[1,2]})
    assert o == {'a':[1,2], 'b':3}

def test_match():
    o = jdic({'e':[{'f':'4'}]})
    assert o.match({'e.f': { '$exists': True }}) == True
    o = jdic({'e':[[0, {'f':'4'}]]})
    assert o.match({'e.f': { '$exists': True }}) == True
    assert o.match({'e.f': { '$exists': False }}) == False
    assert o.match({'e.g': { '$exists': False }}) == True
    assert o.match({'e.f': { '$exists': True }}) == True
    assert o.match({'e.a': { '$exists': True }}) == False
    assert o.match({'a.e': { '$exists': True }}) == False
    o = jdic({'e':[{'f':'4'}]})
    assert o.match({'e.f':'4'}) == True
    assert o.match({'e.f':5}) == False
    assert o.match({'e.f': { '$ne' : 3 }}) == True
    assert o.match({'e.f': { '$gt' : 3 }}) == False
    o = jdic({'e':{'f':4}})
    assert o.match({'e.f': { '$gt' : 3 }}) == True
    assert o.match({'e.f': { '$lt' : 5 }}) == True
    assert o.match({'e.f': { '$lt' : 3 }}) == False
    assert o.match({'e.f': { '$gt' : '3' }}) == False
    assert o.match({'e.f': { '$gte' : '3' }}) == False
    assert o.match({'e.f': { '$gte' : 3 }}) == True
    assert o.match({'e.z': { '$gte' : 3 }}) == False
    o = jdic({'e':4})
    assert o.match({'f':'5'}) == False
    assert o.match({'e':4}) == True
    o = jdic([{'e':4}])
    assert o.match({'e':4}) == True
    assert o.match({'e':'4'}) == False
    assert o.match({'f':'5'}) == False
    assert o.match({'0.e':4}) == True
    o = jdic({'e':[0, 1, {'f':1}]})
    assert o.match({'e':{'$in':[0]}}) == True
    assert o.match({'e':{'$in':[0, 555]}}) == True
    assert o.match({'e':{'$in':[555, 556]}}) == False
    assert o.match({'e.2':{'$in':[{'f':1}]}}) == True
    assert o.match({'e.1':{'$in':[{'f':1}]}}) == False
    assert o.match({'e.1':{'$nin':[{'f':2}]}}) == True
    assert o.match({'e.2':{'$nin':[{'f':2}]}}) == True
    assert o.match({'e.2':{'$ne':None}}) == True
    assert o.match({'e.2':{'$gt':None}}) == False

def test_dict_match():
    o, p = new(), new(asdict = True)
    assert o == p

def test_dict_unmatch():
    o, p = new(), new(asdict = True)
    o['a'] = 0
    assert o != p
