from jdic import settings, jdic
from copy import copy, deepcopy

def new(asdict = False, schema = None, serializer = None, driver = None):
    o = {
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
    return jdic(o, schema = schema, serializer = serializer, driver = driver)

def log(*args):
    print("\n-----------------------------------")
    print(*args)
    print("------------------------------------\n\n")

def test_get_value_at_path():
    o = new(driver = 'jsonpath_ng')
    assert o['j[*].a'] == [1, 2]
    assert o['e.*.eb'] == ['ec']
    assert o['g.a.b.`parent`'] == o['g.a']
    for leave in o.leaves():
        o[leave.path]
    assert o['$'] == o

def test_set_value_at_path():
    o = new(driver = 'jsonpath_ng')
    o['j[*].a'] = 0
    assert o['j[*].a'] == [0, 0]
    o['e.*.eb'] = 0
    assert o['e.*.eb'] == [0]
