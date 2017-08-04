from jsonpath_ng import jsonpath, parse
from collections import Mapping, Sequence
from mongoquery import Query

class Driver():
    _root_strings = [ '$' ]

    def __init__(self):
        self._invalid_keys_startswith = [ '$' ]
        self._invalid_keys_contains = [ '`', ']', '[', '$', '*', '.' ]

    def _key_obj(self, k, obj):
        if k == '' or isinstance(obj, Mapping):
            return k, obj
        elif isinstance(obj, Sequence):
            return int(k), obj
        raise KeyError('Key "{}" was not found in object'.format(k))

    def is_root_path(self, path):
        return path in self._root_strings

    def is_a_path(self, key):
        if isinstance(key, str):
            for c in self._invalid_keys_contains:
                if key.find(c) != -1:
                    return True
        return False

    def get_new_path(self):
        return '$'
                            
    # Transform keys into a single path
    def keys_to_path(self, keys):
        p = '$'
        for k in keys:
            if type(k) is int:
                p += '.[{}]'.format(k)
            else:
                p += '.{}'.format(k)
        return p

    # Transforms a str path to series of keys
    def path_to_keys(self, path):
        if type(path) is not str:
            return [ str(path) ]
        keys = list(path.split('.'))
        for i, k in enumerate(keys):
            if k.startswith('['):
                k = int(k[1:-1])
            keys[i] = k
        if keys[0] == '$':
            del(keys[0])
        return keys

    # Updates a path to include a new terminating key / index
    def add_to_path(self, path, key):
        if isinstance(key, int):
            path = path + '.[{}]'.format(key) if path else '[{}]'.format(key)
        else:
            path = path + '.{}'.format(key) if path else key
        return path

    # Returns a single value at path on obj
    def get_value_at_path(self, obj, path):
        jsonpath_expr = parse(path)
        return [m.value for m in jsonpath_expr.find(obj)]

    def get_parent(self, obj, path):
        jsonpath_expr = parse(path)
        childs_path = [m.full_path for m in jsonpath_expr.find(obj)]
        parents = []
        for c_path in childs_path:
            c_path = str(c_path)
            keys = c_path.split('.')
            key = keys[-1]
            parent_path = '.'.join(keys[:-1])
            jsonpath_expr = parse(parent_path)
            try:
                parent = [m.value for m in jsonpath_expr.find(obj)][0]
            except:
                raise Exception('NoParent', 'No parent for path {}'.format(parent_path))
            parents.append((parent, key))
        return parents

    # Receives a string, must raise an error if invalid
    def control_invalid_key(self, k):
        if type(k) not in [str, int]:
            raise KeyError('Forbidden key type "{}"'.format(type(k)))
        if type(k) is str and not k:
            raise KeyError('Key cannot be an empty string')
        for c in self._invalid_keys_startswith:
            if k.startswith(c):
                raise KeyError('Character "{}" forbidden in key "{}"'.format(c, k))
        try:
            c = k[0]
            if c.isdigit():
                raise KeyError('Keys cannot start with a number'.format(c, k))
        except:
            pass
        for c in self._invalid_keys_contains:
            if k.find(c) != -1:
                raise KeyError('Character "{}" forbidden in key "{}"'.format(c, k))

    def match(self, obj, query):
        q = Query(query)
        return q.match(obj)
