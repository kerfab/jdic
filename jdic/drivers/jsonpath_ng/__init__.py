""" The driver on top of jsonpath_ng """

from collections import Mapping, Sequence
from jsonpath_ng import jsonpath, parse
from mongoquery import Query
import jdic.drivers.mongo

class Driver(jdic.drivers.mongo.Driver):
    """ The driver class for Jdic objects """
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
    def control_invalid_key(cls, key):
        # pylint: disable=duplicate-code
        cls._control_str_int_key(key)
        cls._control_startswith(key)
        try:
            char = key[0]
            if char.isdigit():
                raise KeyError('Keys cannot start with a number, "{}"'.format(key))
        except TypeError:
            pass
        cls._control_contains(key)

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
            for char in cls._invalid_keys_contains:
                if key.find(char) != -1:
                    return True
        return False

    @staticmethod
    def keys_to_path(keys):
        path = '$'
        for key in keys:
            if isinstance(key, int):
                path += '.[{}]'.format(key)
            else:
                path += '.{}'.format(key)
        return path

    @staticmethod
    def path_to_keys(path):
        if not isinstance(path, str):
            return [str(path)]
        keys = list(path.split('.'))
        for ind, key in enumerate(keys):
            if key.startswith('['):
                key = int(key[1:-1])
            keys[ind] = key
        if keys[0] == '$':
            del keys[0]
        return keys
