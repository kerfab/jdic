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
    def _control_str_int_key(key):
        if isinstance(key, str) and not key:
            raise KeyError('Key cannot be an empty string')
        if not isinstance(key, str) and not isinstance(key, int):
            raise KeyError('Forbidden key type "{}"'.format(type(key)))

    @classmethod
    def _control_startswith(cls, key):
        if not isinstance(key, str):
            return
        for char in cls._invalid_keys_startswith:
            if key.startswith(char):
                raise KeyError('Character "{}" forbidden in key "{}"'
                               .format(char, key))

    @classmethod
    def _control_contains(cls, key):
        if not isinstance(key, str):
            return
        for char in cls._invalid_keys_contains:
            if key.find(char) != -1:
                raise KeyError('Character "{}" forbidden in key "{}"'.format(char, key))

    @staticmethod
    def _key_obj(key, obj):
        """Returns the object and the key, with key type transformed according
        to object type.
        """
        if key == '' or isinstance(obj, Mapping):
            return key, obj
        elif isinstance(obj, Sequence):
            return int(key), obj
        raise KeyError('Key "{}" was not found in object'.format(key))

    @classmethod
    def add_to_path(cls, path, key):
        """Add a key at the end of a JSON path"""
        cls.control_invalid_key(key)
        if path:
            return path + '.' + str(key)
        return str(key)

    @classmethod
    def control_invalid_key(cls, key):
        """ Raises an exception if a key format is not valid """
        cls._control_str_int_key(key)
        cls._control_startswith(key)
        cls._control_contains(key)

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
        if not isinstance(path, str):
            return str(path)
        return list(path.split('.'))
