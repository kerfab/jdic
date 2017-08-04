from collections import Mapping, Sequence
from jdic.mongoquery.mongoquery import Query
from jdic import jdic

class Driver():
    _root_strings = [ '' ]

    def __init__(self):
        self._invalid_keys_startswith = [ '$' ]
        self._invalid_keys_contains = [ '.' ]

    def _key_obj(self, k, obj):
        if k == '' or isinstance(obj, Mapping):
            return k, obj
        elif isinstance(obj, Sequence):
            return int(k), obj
        raise KeyError('Key "{}" was not found in object'.format(k))

    def is_root_path(self, path):
        return path in self._root_strings

    def is_a_path(self, key):
        if isinstance(key, str) and (key == '' or key.find('.') != -1):
            return True
        return False

    def get_new_path(self):
        return ''

    # Transform keys into a single path
    def keys_to_path(self, keys):
        p = ''
        for k in keys:
            p += '.'+str(k) if p else str(k)
        return p

    # Transforms a str path to series of keys
    def path_to_keys(self, path):
        if type(path) is not str:
            return str(path)
        return list(path.split('.'))

    # Updates a path to include a new terminating key / index
    def add_to_path(self, path, key):
        if path:
            return path + '.' + str(key)
        return str(key)

    # Returns a single value at path on obj
    def get_value_at_path(self, obj, path):
        keys_lists = self.path_to_keys(path)
        for k in keys_lists:
            k, obj = self._key_obj(k, obj)
            obj = obj[k]
        return obj

    def get_parent(self, obj, path):
        keys = self.path_to_keys(path)
        nb_keys = len(keys)
        for i, k in enumerate(keys):
            if i == nb_keys - 1:
                k, obj = self._key_obj(keys[-1], obj)
                return [ (obj, k) ]
            try:
                k, obj = self._key_obj(k, obj)
                obj = obj[k]
            except:
                break
        raise Exception('NoParent', 'No parent for path {}'.format(path))

    # Receives a string, must raise an error if invalid
    def control_invalid_key(self, k):
        if type(k) not in [str, int]:
            raise KeyError('Forbidden key type "{}"'.format(type(k)))
        if type(k) is str and not k:
            raise KeyError('Key cannot be an empty string')
        for c in self._invalid_keys_startswith:
            if k.startswith(c):
                raise KeyError('Character "{}" forbidden in key "{}"'.format(c, k))
        for c in self._invalid_keys_contains:
            if k.find(c) != -1:
                raise KeyError('Character "{}" forbidden in key "{}"'.format(c, k))
                
    def match(self, obj, query):
        if not isinstance(obj, Sequence) and not isinstance(obj, Mapping):
            return False
        q = Query(query)
        return q.match(obj)
