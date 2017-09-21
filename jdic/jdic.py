"""
The Jdic module provides the features required to manipulate
JSON objects through a consistent API.
"""
import json
import hashlib
import importlib
from collections import Sequence, Mapping
import json_delta
import jsonschema
import jdic.drivers # pylint: disable=unused-import
from . import settings


JSON_ITERABLES = [
    Mapping,
    Sequence
]

JSON_LEAVES = [
    str,
    int,
    float,
    bool,
    type(None)
]

class MatchResult(object):
    """ Wraps the results of searches and browses within Jdic objects """
    # pylint: disable=too-few-public-methods

    def __init__(self, **kwargs):
        self._obj = {}
        for k in kwargs:
            setattr(self, k, kwargs[k])
            self._obj[k] = kwargs[k]

    def __str__(self):
        return str(self._obj)

    def __iter__(self):
        yield from self._obj.__iter__()

    def __getitem__(self, item):
        return self._obj[item]



class Jdic(object):
    """
    The Jdic class provides the useful operations to crawl or manipulate JSON data objects.
    Do not instantiate this class directly, use the instantation wrapper function `jdic()` instead
    """
    # pylint: disable=too-many-instance-attributes

    _attr_whitelist = [
        'count',
        'index',
        'copy',
        'fromkeys',
        'keys',
        'items',
        'values'
    ]

    ##
    # CLASS OPERATORS
    ##

    def __init__(self, iterable, schema=None, serializer=None, driver=None,
                 _parent=None, _key=None):
        """ Instantiates a Generic Jdic object.

        iterable: the core data to be contained within a Jdic (usually dict or list)
        schema: a JSON schema which may be used for automatic validation of data
        serializer: a function which might be used for custom-made data-to-JSON serialization
        driver: the class which implements the driver features
        _parent: used internally to attach a new Jdic to another. Within a JSON hierarchy all
                 iterables are Jdic objects.
        _key: used internally to indicate under which key (or index) the new Jdic is attached
              within its parent.
        """
        # pylint: disable=protected-access
        self._parent = _parent
        self._key = _key
        # Load / Inherit driver first
        if self._parent is None:
            self._driver_name = driver if driver else settings.json_path_driver
            self._driver = None
        else:
            self._driver_name = self._parent._driver_name if driver is None else driver
            self._driver = self._parent._driver if driver is None else None
        if self._driver is None:
            self._driver = importlib.import_module('.'+self._driver_name, 'jdic.drivers').Driver()
        # Inherit parent or constructor properties
        if self._parent is None:
            self._path = self._driver.get_new_path()
            self._serializer = serializer
            self._depth = 0
        else:
            self._path = self._driver.add_to_path(self._parent._path, self._key)
            self._serializer = self._parent._serializer if serializer is None else serializer
            self._depth = self._parent._depth + 1
        self._schema = schema
        self._cache = {}
        # Dereference or cast to strict Json
        if isinstance(iterable, Jdic):
            iterable = iterable._obj
        self._obj = self._serialize_to_jdic(iterable, parent=self)
        if self._schema:
            self.validate(self._schema)

    def __copy__(self):
        return self.new()

    def __deepcopy__(self, _):
        return self.new()

    def __delitem__(self, path):
        # pylint: disable=protected-access
        if self._driver.is_root_path(path):
            if isinstance(self._obj, Mapping):
                self._obj = {}
            else:
                self._obj = []
            self._flag_modified()
            return
        if self._driver.is_a_path(path):
            parents = self._driver.get_parent(self._obj, path)
        else:
            parents = [(self, path)]
        for parent, key in parents:
            del parent._obj[key]
            parent._flag_modified()

    def __eq__(self, obj):
        if isinstance(obj, Jdic):
            return self.checksum() == obj.checksum()
        elif self._is_iterable(obj):
            return self.checksum() == jdic_create(obj).checksum()
        return False

    def __getattr__(self, attr):
        attr = getattr(self._obj, attr)
        if attr not in self._attr_whitelist:
            self._flag_modified()
        return attr

    def __getitem__(self, item):
        if self._driver.is_root_path(item):
            return self
        if self._driver.is_a_path(item):
            return self._driver.get_value_at_path(self._obj, item)
        if isinstance(self._obj, Mapping):
            return self._obj[str(item)]
        return self._obj[int(item)]

    def __iter__(self):
        yield from self._obj.__iter__()

    def __len__(self):
        return len(self._obj)

    def __setitem__(self, path, value):
        # pylint: disable=protected-access
        if self._driver.is_root_path(path):
            if not self._is_iterable(value):
                raise ValueError('Cannot reassign object to non iterable "{}"'.format(type(value)))
            self._jdic_reload(value)
        if self._driver.is_a_path(path):
            parents = self._driver.get_parent(self._obj, path)
        else:
            parents = [(self, path)]
        for parent, key in parents:
            if self._is_iterable(value):
                value = jdic_create(value, _parent=parent, _key=key)
            parent._obj[key] = value
            parent._flag_modified()

    def __str__(self):
        return self.json(sort_keys=settings.json_dump_sort_keys,
                         indent=settings.json_dump_indent, ensure_ascii=False)

    __repr__ = __str__

    ##
    # UNDERLYING FUNCTIONS
    ##

    def _flag_modified(self):
        # pylint: disable=protected-access
        self._cache = {}
        if self._parent is not None:
            self._parent._flag_modified()
        if self._schema:
            self.validate(self._schema)

    def _input_serialize(self, obj):
        if self._serializer:
            obj = self._serializer(obj)
        elif callable(settings.serialize_custom_function):
            # pylint: disable=not-callable
            obj = settings.serialize_custom_function(obj)
        if isinstance(obj, float) and settings.serialize_float_to_int and int(obj) == obj:
            return int(obj)
        if self._is_json_leaf(obj):
            return obj
        if isinstance(obj, Mapping):
            return dict(obj)
        elif isinstance(obj, Sequence):
            return list(obj)
        return str(obj)

    def _is_iterable(self, obj):
        if self._is_json_leaf(obj):
            return False
        for itype in JSON_ITERABLES:
            if isinstance(obj, itype):
                return True
        return False

    @staticmethod
    def _is_json_leaf(obj):
        """ True for int, float, str, bool, None """
        for ltype in JSON_LEAVES:
            if isinstance(obj, ltype):
                return True
        return False

    @staticmethod
    def _is_limit_reached(number, limit):
        """ Helper function """
        if limit is None:
            return False
        if limit < 0:
            return False
        if limit >= number:
            return True

    def _jdic_reload(self, obj):
        # pylint: disable=protected-access
        if isinstance(obj, Jdic):
            obj = obj._obj
        self._obj = self._serialize_to_jdic(obj, parent=self)
        self._flag_modified()

    @staticmethod
    def _keys_in(obj, keys, mode):
        """ Helper function """
        if not isinstance(obj, Mapping):
            return False
        if mode == "any":
            for key in keys:
                if key in obj:
                    return True
            return False
        elif mode == "all":
            for key in keys:
                if key not in obj:
                    return False
            return True
        raise NotImplementedError(mode)

    def _match(self, obj, query):
        return self._driver.match(obj, query)

    def _merge(self, obj, with_obj, arr_mode="replace"):
        # pylint: disable=protected-access
        if isinstance(obj, Jdic):
            obj = obj._obj
        if isinstance(with_obj, Jdic):
            with_obj = with_obj._obj
        if not self._is_iterable(obj) or not self._is_iterable(with_obj):
            raise TypeError('Cannot merge {} with {}'.format(type(obj), type(with_obj)))
        unique_t = self._unique_type(obj, with_obj)
        if not unique_t:
            return with_obj
        if unique_t and isinstance(obj, Mapping):
            obj = self._merge_dicts(obj, with_obj, arr_mode)
        else:
            obj = self._merge_arrays(obj, with_obj, arr_mode)
        return obj

    def _merge_arrays(self, arr, with_arr, mode="replace"):
        if mode == "replace":
            return with_arr
        if mode == "append":
            return arr + with_arr
        if mode == "new":
            for val in with_arr:
                if val not in arr:
                    arr.append(val)
            return arr
        if mode == "merge":
            arr_l = len(arr)
            for index, val in enumerate(with_arr):
                if index >= arr_l:
                    arr.append(val)
                else:
                    if self._is_iterable(arr[index]) and self._is_iterable(with_arr[index]):
                        arr[index] = self._merge(arr[index], with_arr[index], mode)
                    else:
                        arr[index] = with_arr[index]
            return arr
        raise NotImplementedError('Merge array mode "{}" not implemented'.format(mode))

    def _merge_dicts(self, dic, with_dic, arr_mode):
        for k in with_dic:
            if k not in dic:
                dic[k] = with_dic[k]
            else:
                if self._is_iterable(dic[k]) and self._is_iterable(with_dic[k]):
                    dic[k] = self._merge(dic[k], with_dic[k], arr_mode)
                else:
                    dic[k] = with_dic[k]
        return dic

    def _serialize_to_jdic(self, iterable, parent=None):
        if isinstance(iterable, Mapping):
            iterable = dict(iterable)
        elif isinstance(iterable, Sequence):
            iterable = list(iterable)
        res = type(iterable)()
        for key, val in jdic_enumerate(iterable):
            if isinstance(res, dict):
                key = str(key)
            val = self._input_serialize(val)
            if self._is_iterable(val):
                val = jdic_create(val, _parent=parent, _key=key)
            if isinstance(res, dict):
                res[key] = val
            else:
                res.append(val)
        return res

    @staticmethod
    def _unique_type(*args):
        result = None
        for val in args:
            type_val = type(val)
            if not result:
                result = type_val
            elif result != type_val:
                return None
        return result

    ##
    # PUBLIC FUNCTIONS
    ##

    def browse(self, sort=False, depth=None, maxdepth=None, _start=True):
        """
        Iterates on each JSON entry in a recursive fashion

        Arguments:
          - sort: bool. If True keys in dicts are alphabetically sorted before values are yielded.
          - depth: an integer between 0 and +inf. Results are only yielded at this depth.
          - maxdepth: an integer between 0 and +inf. Results won't be yielded past this depth.
        """
        # pylint: disable=protected-access
        if maxdepth is not None and maxdepth >= 0 and self._depth > maxdepth:
            return
        if depth is not None and self._depth > depth:
            return
        parent_path = None if self._parent is None else self._parent._path
        if depth is None and _start:
            yield MatchResult(parent=self._parent, parent_path=parent_path, key=self._key,
                              value=self, path=self._path, depth=self._depth)
        for key, val in jdic_enumerate(self._obj, sort=sort):
            path = self._driver.add_to_path(self._path, key)
            if depth is None or depth == self._depth:
                yield MatchResult(parent=self, parent_path=self._path, key=key,
                                  value=val, path=path, depth=self._depth)
            if isinstance(val, Jdic):
                yield from val.browse(sort=sort, depth=depth, maxdepth=maxdepth, _start=False)

    def checksum(self, algo='sha256'):
        """ Returns an ASCII hexadecimal checksum representing the state of the object """
        if 'checksum' in self._cache:
            return self._cache['checksum']
        hash_ = hashlib.new(algo)
        hash_.update(type(self._obj).__name__.encode('utf-8'))
        for key, val in jdic_enumerate(self._obj, sort=True):
            if isinstance(val, Jdic):
                data = "{}:{}:{}:{}".format(type(key).__name__, key,
                                            type(val).__name__, val.checksum())
            else:
                data = "{}:{}:{}:{}".format(type(key).__name__, key,
                                            type(val).__name__, val)
            hash_.update(data.encode('utf-8'))
        checksum = hash_.hexdigest()
        self._cache['checksum'] = checksum
        return checksum

    def deepness(self):
        """ Returns an integer representing how deep the Jdic object is """
        if 'deepness' in self._cache:
            return self._cache['deepness']
        deepness = 0
        for val in self.browse():
            if isinstance(val.value, Jdic):
                depth = val.value.depth()
                if depth > deepness:
                    deepness = depth
        self._cache['deepness'] = deepness
        return deepness

    def depth(self):
        """ Returns an integer representing the depth of the current Jdic object """
        return self._depth

    def diff(self, obj):
        """ Returns a delta between this object and obj """
        if isinstance(obj, Jdic):
            obj = obj.raw()
        return json_delta.diff(self.raw(), obj, verbose=False)

    def enumerate(self, sort=False):
        """ Yields a key, value pair with both Jdic Mappings and Sequences """
        yield from jdic_enumerate(self._obj, sort=sort)

    def find(self, value, limit=None, sort=False, depth=None, maxdepth=None):
        """ Finds a value within the Jdic object, the search is recursive """
        # pylint: disable=too-many-arguments
        if limit == 0:
            return
        num = 0
        for res in self.browse(sort=sort, depth=depth, maxdepth=maxdepth):
            if res.value == value:
                yield res
                num += 1
                if self._is_limit_reached(num, limit):
                    return

    def find_keys(self, keys, mode="any", sort=False,
                  limit=None, depth=None, maxdepth=None):
        """ Find one or multiple keys within the Jdic object """
        # pylint: disable=too-many-arguments
        if limit is not None and limit == 0:
            return
        if not isinstance(keys, list):
            keys = [keys]
        num = 0
        for match in self.browse(sort=sort, depth=depth, maxdepth=maxdepth):
            if isinstance(match.value, Jdic):
                if self._keys_in(match.value, keys, mode):
                    yield match
                    num += 1
                    if limit is not None and limit == num:
                        return

    def find_match(self, query, sort=False, limit=None, depth=None, maxdepth=None):
        """ Find inner data which match the provided query """
        # pylint: disable=too-many-arguments
        if limit == 0 or not maxdepth == 0:
            return
        num = 0
        for res in self.browse(sort=sort, depth=depth, maxdepth=maxdepth):
            if self._match(res.value, query):
                yield res
                num += 1
                if self._is_limit_reached(num, limit):
                    break

    def json(self, sort_keys=False, indent=0, ensure_ascii=False):
        """ Returns a string of the object in JSON format """
        return json.dumps(self.raw(), sort_keys=sort_keys,
                          indent=indent, ensure_ascii=ensure_ascii)

    def leaves(self, sort=False, depth=None, maxdepth=None):
        """ Iterates recursively, raises leaves of the object only """
        for res in self.browse(sort=sort, depth=depth, maxdepth=maxdepth):
            if self._is_json_leaf(res.value):
                yield res

    def nb_leaves(self):
        """ Return an integer, the number of leaves within the Jdic object """
        if 'nb_leaves' in self._cache:
            return self._cache['nb_leaves']
        nb_leaves = 0
        for _ in self.leaves():
            nb_leaves += 1
        self._cache['nb_leaves'] = nb_leaves
        return nb_leaves

    def match(self, query):
        """ Returns True if the object matches against query, False otherwise """
        return self._match(self._obj, query)

    def merge(self, *args, arr_mode="replace"):
        """ Make a deep merge of the current Jdic object with one or more objects """
        for with_obj in args:
            if (isinstance(with_obj, Mapping) and not isinstance(self._obj, Mapping)) or\
               (not isinstance(with_obj, Mapping) and isinstance(self._obj, Mapping)):
                raise TypeError('Cannot merge "{}" with "{}"'.format(
                    type(self._obj),
                    type(with_obj)))
            result = self._merge(self._obj, with_obj, arr_mode)
            self._jdic_reload(result)
        return self

    def new(self, _obj=None):
        """ Returns a copy of the current object """
        if _obj is None:
            _obj = self._obj
        return jdic_create(_obj, serializer=self._serializer,
                           driver=self._driver_name, schema=self._schema)

    def parent(self, generation=1):
        """ Returns the Jdic object parent of this object """
        # pylint: disable=protected-access
        if generation < 1:
            return None
        res = self._parent
        while generation > 1 and res is not None:
            res = res._parent
            generation = generation - 1
        return res

    def patch(self, diff):
        """ Takes a delta (from diff()) and applies it to update the object """
        if not diff:
            return
        res = json_delta.patch(self.raw(), diff)
        if self._is_iterable(res):
            return self.new(res)
        return res

    def path(self):
        """ Return the path of the current Jdic object within its hierarchy """
        return self._path

    def raw(self, _obj=None, _cache=False):
        """ Returns a copy of the current object in basic Python types """
        if _cache and 'raw' in self._cache:
            return self._cache['raw']
        obj = _obj if _obj else self._obj
        res = type(obj)()
        for key, val in jdic_enumerate(obj):
            if isinstance(val, Jdic):
                val = val.raw(_cache=_cache)
            if isinstance(res, dict):
                res[key] = val
            else:
                res.append(val)
        self._cache['raw'] = res
        return res

    def validate(self, schema=None):
        """ Validates the current Jdic object against a JSON schema """
        if schema is not None:
            return jsonschema.validate(self.raw(), schema)
        elif schema is None and self._schema is not None:
            return jsonschema.validate(self.raw(), self._schema)
        raise ValueError('The current object is not supervised by any schema')



class JdicSequence(Jdic, Sequence):
    """ A wrapper for Jdics with Sequence root types (usually list) """

class JdicMapping(Jdic, Mapping):
    """ A wrapper for Jdics with Mapping root types (usually dict) """


def jdic_create(iterable, **kwargs):
    """ This function returns a Jdic correctly typped according to the data root type """
    if isinstance(iterable, Mapping):
        return JdicMapping(iterable, **kwargs)
    elif isinstance(iterable, Sequence):
        return JdicSequence(iterable, **kwargs)
    else:
        raise ValueError('Cannot create Jdic object from "{}"'.format(type(iterable)))

def jdic_enumerate(obj, sort=False):
    """ Will enumerate dicts and list in a similar fashion, to ease iterables browsing """
    if isinstance(obj, Mapping):
        try:
            keys = sorted(obj.keys()) if sort else obj
        except TypeError:
            keys = sorted(dict(obj).keys()) if sort else obj
        for k in keys:
            yield (k, obj[k])
    elif isinstance(obj, Sequence):
        ind = 0
        for val in obj:
            yield (ind, val)
            ind += 1
    else:
        raise TypeError('Cannot enumerate objects of type "{}"'.format(type(obj)))
