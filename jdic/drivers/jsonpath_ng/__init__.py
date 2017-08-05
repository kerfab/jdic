import jdic.drivers.mongo
from jsonpath_ng import jsonpath, parse
from collections import Mapping, Sequence
from mongoquery import Query

class Driver(jdic.drivers.mongo.Driver):
    _root_strings = ['$']
    _invalid_keys_startswith = ['$']
    _invalid_keys_contains = ['`', ']', '[', '$', '*', '.']

    @classmethod
    def add_to_path(cls, path, key):
        cls.control_invalid_key(key)
        if isinstance(key, int):
            path = path + '.[{}]'.format(key) if path else '[{}]'.format(key)
        else:
            path = path + '.{}'.format(key) if path else key
        return path

    @classmethod
    def control_invalid_key(cls, k):
        if type(k) not in [str, int]:
            raise KeyError('Forbidden key type "{}"'.format(type(k)))
        if type(k) is int:
            return
        if type(k) is str and not k:
            raise KeyError('Key cannot be an empty string')
        for char in cls._invalid_keys_startswith:
            if k.startswith(char):
                raise KeyError('Character "{}" forbidden in key "{}"'.format(char, k))
        try:
            char = k[0]
            if char.isdigit():
                raise KeyError('Keys cannot start with a number'.format(char, k))
        except:
            pass
        for char in cls._invalid_keys_contains:
            if k.find(char) != -1:
                raise KeyError('Character "{}" forbidden in key "{}"'.format(char, k))

    @staticmethod
    def get_new_path():
        return '$'

    @staticmethod
    def get_parent(obj, path):
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

    @staticmethod
    def get_value_at_path(obj, path):
        jsonpath_expr = parse(path)
        return [m.value for m in jsonpath_expr.find(obj)]

    @classmethod
    def is_a_path(cls, key):
        if isinstance(key, str):
            for c in cls._invalid_keys_contains:
                if key.find(c) != -1:
                    return True
        return False

    @staticmethod
    def keys_to_path(keys):
        p = '$'
        for k in keys:
            if type(k) is int:
                p += '.[{}]'.format(k)
            else:
                p += '.{}'.format(k)
        return p

    @staticmethod
    def path_to_keys(path):
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
