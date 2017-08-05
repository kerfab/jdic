"""The Mongo driver for Jdic"""

from collections import Mapping, Sequence
from mongoquery import Query
from jdic import jdic

class Driver(object):
    """The driver class"""
    _root_strings = ['']
    _invalid_keys_startswith = ['$']
    _invalid_keys_contains = ['.']

    @staticmethod
    def _key_obj(k, obj):
        """Returns the object and the key, with key type transformed according
        to object type.
        """
        if k == '' or isinstance(obj, Mapping):
            return k, obj
        elif isinstance(obj, Sequence):
            return int(k), obj
        raise KeyError('Key "{}" was not found in object'.format(k))

    @classmethod
    def add_to_path(cls, path, key):
        """Add a key at the end of a JSON path"""
        cls.control_invalid_key(key)
        if path:
            return path + '.' + str(key)
        return str(key)

    @classmethod
    def control_invalid_key(cls, k):
        """Raises an exception if a key format is not valid"""
        if type(k) not in [str, int]:
            raise KeyError('Forbidden key type "{}"'.format(type(k)))
        if type(k) is int:
            return
        if type(k) is str and not k:
            raise KeyError('Key cannot be an empty string')
        for char in cls._invalid_keys_startswith:
            if k.startswith(char):
                raise KeyError('Character "{}" forbidden in key "{}"'
                               .format(char, k))
        for char in cls._invalid_keys_contains:
            if k.find(char) != -1:
                raise KeyError('Character "{}" forbidden in key "{}"'
                               .format(char, k))

    @staticmethod
    def get_new_path():
        """Returns a JSON path pointing to root of document"""
        return ''

    @classmethod
    def get_parent(cls, obj, path):
        """Returns the parent of the value pointed by JSON path"""
        keys = cls.path_to_keys(path)
        nb_keys = len(keys)
        for i, k in enumerate(keys):
            if i == nb_keys - 1:
                k, obj = cls._key_obj(keys[-1], obj)
                return [(obj, k)]
            try:
                k, obj = cls._key_obj(k, obj)
                obj = obj[k]
            except (TypeError, IndexError):
                break
        raise Exception('NoParent', 'No parent for path {}'.format(path))

    @classmethod
    def get_value_at_path(cls, obj, path):
        """Returns the value pointed by JSON path"""
        keys_lists = cls.path_to_keys(path)
        for k in keys_lists:
            k, obj = cls._key_obj(k, obj)
            obj = obj[k]
        return obj

    @staticmethod
    def is_a_path(key):
        """True if is a JSON path, else False"""
        if isinstance(key, str) and (key == '' or key.find('.') != -1):
            return True
        return False

    @classmethod
    def is_root_path(cls, path):
        """True if is a JSON path for root document, else False"""
        return path in cls._root_strings

    @staticmethod
    def keys_to_path(keys):
        """Transforms a list of keys into a proper JSON path"""
        path = ''
        for k in keys:
            path += '.'+str(k) if path else str(k)
        return path

    @staticmethod
    def match(obj, query):
        """Returns True if object matches the mongo query, else False"""
        if not isinstance(obj, Sequence) and not isinstance(obj, Mapping):
            return False
        query = Query(query)
        return query.match(obj)

    @staticmethod
    def path_to_keys(path):
        """Transforms an expression-less JSON path into a series of keys"""
        if type(path) is not str:
            return str(path)
        return list(path.split('.'))
