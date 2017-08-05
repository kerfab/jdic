import json
import re
import hashlib
import random
from . import settings
import importlib
from . import drivers
import json_delta
import jsonschema
from collections import Sequence, Mapping, MutableSequence, MutableMapping

_json_iterables_types = [
    Mapping,
    Sequence
]

_json_leaves_types = [
    str,
    int,
    float,
    bool,
    type(None)
]

class MatchResult:
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

class Jdic:

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

    """
    kwargs:
      driver
      schema
      serializer
      _parent
      _key
    """
    def __init__(self, iterable, schema = None, serializer = None, driver = None,
                 _parent = None, _key = None):
        self._parent = _parent
        self._key = _key
        # Load / Inherit driver first
        if self._parent == None:
            self._driver_name = driver if driver else settings.json_path_driver
            self._driver = None
        else:
            self._driver_name = self._parent._driver_name if driver == None else driver
            self._driver = self._parent._driver if driver == None else None
        if self._driver == None:
            self._driver = importlib.import_module('.'+self._driver_name, 'jdic.drivers').Driver()
        # Inherit parent or constructor properties
        if self._parent == None:
            self._path = self._driver.get_new_path()
            self._serializer = serializer
            self._depth = 0
        else:
            self._path = self._driver.add_to_path(self._parent._path, self._key)
            self._serializer = self._parent._serializer if serializer == None else serializer
            self._depth = self._parent._depth + 1
        self._schema = schema
        self._cache = {}
        # Dereference or cast to strict Json
        if isinstance(iterable, Jdic):
            iterable = iterable._obj
        self._obj = self._serialize_to_jdic(iterable, parent = self)
        if self._schema:
            self.validate(self._schema)

    def __copy__(self):
        return self.new()

    def __deepcopy__(self, _ignored = None):
        return self.new()

    def __delitem__(self, path):
        if self._driver.is_root_path(path):
            if isinstance(self._obj, Mapping):
                self._obj = {}
            else:
                self.obj = []
            self._flag_modified()
            return
        if self._driver.is_a_path(path):
            parents = self._driver.get_parent(self._obj, path)
        else:
            parents = [ (self, path) ]
        for parent, key in parents:
            del(parent._obj[key])
            parent._flag_modified()

    def __eq__(self, obj):
        if isinstance(obj, Jdic):
            return self.checksum() == obj.checksum()
        elif self._is_iterable(obj):
            return self.checksum() == jdic(obj).checksum()
        return False

    def __getattr__(self, attr):
        try:
            return getattr(self, attr)
        except:
            pass
        a = getattr(self._obj, attr)
        if attr not in self._attr_whitelist:
            self._flag_modified()
        return a

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
        if self._driver.is_root_path(path):
            if not self._is_iterable(value):
                raise ValueError('Cannot reassign object to non iterable "{}"'.format(type(value)))
            self._jdic_reload(value)
        if self._driver.is_a_path(path):
            parents = self._driver.get_parent(self._obj, path)
        else:
            parents = [ (self, path) ]
        for parent, key in parents:
            if self._is_iterable(value):
                parent_path_keys = self._driver.path_to_keys(parent._path)
                child_path = self._driver.keys_to_path(parent_path_keys + [ key ])
                value = jdic(value, _parent = parent, _key = key)
            parent._obj[key] = value
            parent._flag_modified()

    def __str__(self):
        return self.json(sort_keys = settings.json_dump_sort_keys,
                         indent = settings.json_dump_indent, ensure_ascii = False)

    __repr__ = __str__

    ##
    # UNDERLYING FUNCTIONS
    ## 

    def _flag_modified(self):
        self._cache = {}
        if self._parent != None:
            self._parent._flag_modified()
        if self._schema:
            self.validate(self._schema)

    def _input_serialize(self, obj, copy = False, parent = None):
        if self._serializer:
            obj = self._serializer(obj)
        elif settings.serialize_custom_function:
            obj = settings.serialize_custom_function(obj)
        if isinstance(obj, float) and settings.serialize_float_to_int and int(obj) == obj:
            return int(obj)
        if type(obj) in _json_leaves_types:
            return obj
        if isinstance(obj, Mapping):
            return dict(obj)
        elif isinstance(obj, Sequence):
            return list(obj)
        return str(obj)

    def _is_iterable(self, obj):
        if self._is_json_leaf(obj):
            return False
        for t in _json_iterables_types:
            if isinstance(obj, t):
                return True
        return False

    def _is_json_leaf(self, obj):
        for t in _json_leaves_types:
            if isinstance(obj, t):
                return True
        return False

    def _is_limit_reached(self, nb, limit):
        if limit == None:
            return False
        if limit < 0:
            return False
        if limit >= nb:
            return True

    def _jdic_reload(self, obj):
         if isinstance(obj, Jdic):
             obj = obj._obj
         self._obj = self._serialize_to_jdic(obj, parent = self)
         self._flag_modified()

    def _keys_in(self, obj, keys, mode):
        if not isinstance(obj, Mapping):
            return False
        if mode == "any":
            for k in keys:
                if k in obj:
                    return True
            return False
        elif mode == "all":
            for k in keys:
                if k not in obj:
                    return False
            return True
        raise ValueError('Invalid mode')

    def _match(self, obj, query):
        return self._driver.match(obj, query)

    def _merge(self, obj, with_obj, arr_mode = "replace"):
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

    def _merge_arrays(self, arr, with_arr, mode = "replace"):
        if mode == "replace":
            return with_arr
        if mode == "append":
            return arr + with_arr
        if mode == "new":
            for v in with_arr:
                if v not in arr:
                    arr.append(v)
            return arr
        if mode == "merge":
            arr_l = len(arr)
            for i, v in enumerate(with_arr):
                if i >= arr_l:
                    arr.append(v)
                else:
                    if self._is_iterable(arr[i]) and self._is_iterable(with_arr[i]):
                        arr[i] = self._merge(arr[i], with_arr[i], mode)
                    else:
                        arr[i] = with_arr[i]
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

    def _serialize_to_jdic(self, iterable, parent = None):
        if isinstance(iterable, Mapping):
            iterable = dict(iterable)
        elif isinstance(iterable, Sequence):
            iterable = list(iterable)
        r = type(iterable)()
        for k, v in jdic_enumerate(iterable):
            if isinstance(r, dict):
                k = str(k)
            v = self._input_serialize(v)
            if self._is_iterable(v):
                v = jdic(v, _parent = parent, _key = k)
            if isinstance(r, dict):
                r[k] = v
            else:
                r.append(v)
        return r

    def _unique_type(self, *args):
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

    def browse(self, sort = False, depth = None, maxdepth = None, _start = True):
        if maxdepth != None and maxdepth >= 0 and self._depth > maxdepth:
            return
        if depth != None and self._depth > depth:
            return
        parent_path = None if self._parent == None else self._parent._path
        if depth == None and _start:
            yield MatchResult(parent = self._parent, parent_path = parent_path, key = self._key,
                              value = self, path = self._path, depth = self._depth)
        for k, v in jdic_enumerate(self._obj, sort = sort):
            path = self._driver.add_to_path(self._path, k)
            if depth == None or depth == self._depth:
                yield MatchResult(parent = self, parent_path = self._path, key = k, 
                                  value = v, path = path, depth = self._depth)
            if isinstance(v, Jdic):
                yield from v.browse(sort = sort, depth = depth, maxdepth = maxdepth, _start = False)

    def checksum(self, algo='sha256'):
        if 'checksum' in self._cache:
            return self._cache['checksum']
        hash = hashlib.new(algo)
        hash.update(type(self._obj).__name__.encode('utf-8'))
        for k, v in jdic_enumerate(self._obj, sort = True):
            if isinstance(v, Jdic):
                s = "{}:{}:{}:{}".format(type(k).__name__, k, type(v).__name__, v.checksum())
            else:
                s = "{}:{}:{}:{}".format(type(k).__name__, k, type(v).__name__, v)
            hash.update(s.encode('utf-8'))
        checksum = hash.hexdigest()
        self._cache['checksum'] = checksum
        return checksum

    def deepness(self):
        if 'deepness' in self._cache:
            return self._cache['deepness']
        deepness = 0
        for v in self.browse():
            if isinstance(v.value, Jdic):
                c = v.value.depth()
                if c > deepness:
                    deepness = c
        self._cache['deepness'] = deepness
        return deepness

    def depth(self):
        return self._depth

    def diff(self, obj):
        if isinstance(obj, Jdic):
            obj = obj.raw()
        return json_delta.diff(self.raw(), obj, verbose = False)

    def enumerate(self, sort = False):
        yield from jdic_enumerate(self._obj, sort = sort)

    def find(self, value, sort = False, limit = None, depth = None, maxdepth = None):
        if limit == 0:
            return
        nb = 0
        for res in self.browse(sort = sort, depth = depth, maxdepth = maxdepth):
            if res.value == value:
                yield res
                nb += 1
                if self._is_limit_reached(nb, limit):
                    return

    def find_keys(self, keys, mode = "any", sort = False, 
                  limit = None, depth = None, maxdepth = None):
        if type(keys) is not list:
            keys = [ keys ]
        for m in self.browse(sort = sort, depth = depth, maxdepth = maxdepth):
            if isinstance(m.value, Jdic):
                if self._keys_in(m.value, keys, mode):
                    yield m

    def find_match(self, query, sort = False, limit = None, depth = None, maxdepth = None):
        if limit == 0 or not maxdepth == 0:
            return
        nb = 0
        for res in self.browse(sort = sort, depth = depth, maxdepth = maxdepth):
            if self._match(res.value, query):
                yield res
                nb += 1
                if self._is_limit_reached(nb, limit):
                    break

    def json(self, sort_keys = False, indent = 0, ensure_ascii = False):
        return json.dumps(self.raw(), sort_keys=sort_keys, 
                          indent=indent, ensure_ascii=ensure_ascii)

    def leaves(self, sort = False, depth = None, maxdepth = None):
        for res in self.browse(sort = sort, depth = depth, maxdepth = maxdepth):
            if self._is_json_leaf(res.value):
                yield res

    def nb_leaves(self):
        if 'nbleaves' in self._cache:
            return self._cache['nbleaves']
        n = 0
        for l in self.leaves():
            n = n + 1
        self._cache['nbleaves'] = n
        return n

    def match(self, query):
        return self._match(self._obj, query)

    def merge(self, *args, arr_mode = "replace"):
        for with_obj in args:
            if ((isinstance(with_obj, Mapping) and not isinstance(self._obj, Mapping)) or
                (not isinstance(with_obj, Mapping) and isinstance(self._obj, Mapping))):
                raise TypeError('Cannot merge "{}" with "{}"'.format(type(self._obj), type(with_obj)))
            result = self._merge(self._obj, with_obj, arr_mode)
            self._jdic_reload(result)
        return self

    def new(self, _obj = None):
        if _obj == None:
            _obj = self._obj
        return jdic(_obj, serializer = self._serializer,
                    driver = self._driver_name, schema = self._schema)

    def parent(self, generation = 1):
        if generation < 1:
            return None
        res = self._parent
        while generation > 1 and res != None:
            res = res._parent
            generation = generation - 1
        return res

    def patch(self, diff):
        if not diff:
            return
        r = json_delta.patch(self.raw(), diff)
        if self._is_iterable(r):
            return self.new(r)
        return r

    def path(self):
        return self._path

    def raw(self, _obj = None, _cache = False):
        if _cache and 'raw' in self._cache:
            return self._cache['raw']
        obj = _obj if _obj else self._obj
        r = type(obj)()
        for k, v in jdic_enumerate(obj):
            if isinstance(v, Jdic):
                v = v.raw()
            if isinstance(r, dict):
                r[k] = v
            else:
                r.append(v)
        return r

        res = self._output_json_serialize(self._obj)
        self._cache['raw'] = res
        return res

    def validate(self, schema = None):
        if schema != None:
            return jsonschema.validate(self.raw(), schema)
        elif schema == None and self._schema != None:
            return jsonschema.validate(self.raw(), self._schema)
        raise ValueError('The current object is not supervised by any schema')



class JdicSequence(Jdic, Sequence):
    def __init__(self, iterable, **kwargs):
        super().__init__(iterable, **kwargs)



class JdicMapping(Jdic, Mapping):
    def __init__(self, iterable, **kwargs):
        super().__init__(iterable, **kwargs)



def jdic(iterable, **kwargs):
    if isinstance(iterable, Mapping):
        return JdicMapping(iterable, **kwargs)
    elif isinstance(iterable, Sequence):
        return JdicSequence(iterable, **kwargs)
    else:
        raise ValueError('Cannot create Jdic object from "{}"'.format(type(iterable)))

def jdic_enumerate(obj, sort = False):
    if isinstance(obj, Mapping):
        try:
            keys = sorted(obj.keys()) if sort else obj
        except:
            keys = sorted(dict(obj).keys()) if sort else obj
        for k in keys:
            yield (k, obj[k])
    elif isinstance(obj, Sequence):
        i = 0
        for v in obj:
            yield (i, v)
            i += 1
    else:
        raise TypeError('Cannot enumerate objects of type "{}"'.format(type(obj)))

