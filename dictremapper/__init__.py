# -*- coding:utf-8 -*-
from collections import defaultdict, OrderedDict, namedtuple
from importlib import import_module
from functools import partial
import copy


Frame = namedtuple("Frame", "name remapper excludes")


def import_symbol(x):
    module, name = x.rsplit(".", 1)
    m = import_module(module)
    return getattr(m, name)


class Counter(object):
    def __init__(self, i=0):
        self.i = i

    def __call__(self):
        self.i += 1
        return self.i

count = Counter(0)


class LazyMapperCallable(object):
    def __init__(self, path, many=False, excludes=None, wrapper=None, loader=import_symbol):
        self.path = path
        self.wrapper = wrapper
        self.excludes = ExcludeSet(excludes)
        self.many = many
        self.loader = loader

    def __call__(self, data, stack):
        mapper = stack[-1].remapper
        if self.path == "self" or self.path == mapper.__class__.__name__:
            fn = mapper
        elif self.wrapper is not None:
            fn = self.wrapper
        else:
            fn = self.wrapper = self.loader(self.path)(many=self.many, excludes=self.excludes)
        excludes_dict = fn.get_current_excludes_dict(stack, excludes=self.excludes)
        if self.many:
            return fn.as_list(data, stack, excludes_dict)
        else:
            return fn.as_dict(data, stack, excludes_dict)


Self = partial(LazyMapperCallable, "self")


def maybe_list(xs, delimiter="."):
    if hasattr(xs, "split"):
        return xs.split(delimiter)
    else:
        return xs


marker = object()


class Composed(object):
    aggregate = False

    def __init__(self, xs, callback=sum, tmpstate=False, name=None):
        self.xs = xs
        self._i = count()
        self.callback = callback
        self.tmpstate = tmpstate
        self.name = name

    def __call__(self, data, stack):
        ys = [x(data, stack) for x in self.xs]
        return self.callback(*ys)


class Aggregate(object):
    aggregate = True

    def __init__(self, callback, tmpstate=False):
        self._i = count()
        self.tmpstate = tmpstate
        self.callback = callback

    def __call__(self, data):
        return self.callback(data)


class Path(object):
    aggregate = False

    def __init__(self, keys, callback=None, default=marker, tmpstate=False, name=None):
        self._i = count()
        self.default = default
        self.keys = maybe_list(keys)
        self.callback = callback
        self.tmpstate = tmpstate
        self.name = name

    def access(self, data, stack, keys):
        if not keys:
            return data
        else:
            k = keys[0]
            rest_keys = keys[1:]
            if k.endswith("[]"):
                return [self.access(subdata, stack, rest_keys) for subdata in data[k[:-2]]]
            elif k.isdigit():
                return self.access(data[int(k)], stack, rest_keys)
            else:
                return self.access(data[k], stack, rest_keys)

    def __call__(self, data, stack):
        try:
            result = self.access(data, stack, self.keys)
        except KeyError:
            if self.default is marker:
                raise KeyError("{k} is not in {v}".format(k=self.keys, v=data))
            return self.default
        if self.callback is not None:
            if hasattr(self.callback, "many"):  # remapper
                result = self.callback(result, stack=stack)
            else:
                result = self.callback(result)
        return result


class ChangeOrder(object):
    def __init__(self, path):
        self._i = count()
        self.path = path

    def __call__(self, data, stack):
        return self.path(data, stack)

    def __getattr__(self, k):
        return getattr(self.path, k)


EMPTY = {"": set()}


class ExcludeSet(object):
    def __init__(self, excludes):
        if excludes is None:
            self.data = EMPTY
        elif hasattr(excludes, "transform"):
            self.data = excludes
        else:
            self.data = self.transform(excludes)

    def transform(self, excludes):
        d = {}
        for keys in excludes:
            ks = keys.split(".")
            target = d
            for k in ks[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            if "" not in target:
                target[""] = set()
            target[""].add(ks[-1])
        return d

    def merge(self, d):
        return merge_dict(copy.deepcopy(self.data), d)

    def __getitem__(self, k):
        return self.data[k]

    def get(self, k, default=None):
        return self.data.get(k, default)


def merge_dict(d0, d1):  # side effect
    for k, v in d1.items():
        if k not in d0:
            d0[k] = d1[k]
        elif hasattr(v, "keys"):
            merge_dict(d0[k], v)
        else:
            d0[k].update(d1[k])
    return d0


class Shortcut(object):
    def __init__(self, remapper, keys):
        self.remapper = remapper
        self.keys = maybe_list(keys)

    def __call__(self, data):
        return self.access(data, self.keys)

    def access(self, data, keys):
        if not keys:
            return self.remapper(data)
        else:
            k = keys[0]
            rest_keys = keys[1:]
            if k.endswith("[]"):
                return [self.access(subdata, rest_keys) for subdata in data[k[:-2]]]
            elif k.isdigit():
                return self.access(data[int(k)], rest_keys)
            else:
                return self.access(data[k], rest_keys)


class Remapper(object):
    dict = OrderedDict

    def __new__(cls, *args, **kwargs):
        if "_paths" not in cls.__dict__:
            paths = defaultdict(list)
            for c in cls.mro():
                for name, attr in c.__dict__.items():
                    if hasattr(attr, "_i"):  # path
                        paths[name].append(attr)
            cls._paths = OrderedDict((k, v[0]) for k, v in sorted(paths.items(), key=lambda vs: vs[1][0]._i))
        return super(Remapper, cls).__new__(cls)

    def __init__(self, many=False, excludes=None):
        self.many = many
        self.excludes = ExcludeSet(excludes)

    def __call__(self, data, stack=None, excludes_dict=None):
        stack = stack or []
        excludes_dict = excludes_dict or self.get_current_excludes_dict(stack)
        if self.many:
            return self.as_list(data, stack, excludes_dict)
        else:
            return self.as_dict(data, stack, excludes_dict)

    def as_list(self, dataset, stack, excludes_dict):
        return [self.as_dict(data, stack, excludes_dict) for data in dataset]

    def get_current_excludes_dict(self, stack, excludes=None):
        excludes = excludes or self.excludes
        if not stack:
            return excludes
        return excludes.merge(stack[-1].excludes)

    def as_dict(self, data, stack, excludes_dict):
        d = self.dict()
        dummy = object()
        lazies = []
        excludes = excludes_dict.get("", [])

        for name, path in self._paths.items():
            if name in excludes:
                continue
            name = path.name or name
            if path.aggregate:
                lazies.append((name, path))
                d[name] = dummy
            else:
                stack.append(Frame(name=name, remapper=self, excludes=excludes_dict.get(name, EMPTY)))
                d[name] = path(data, stack)
                stack.pop()
        for name, path in lazies:
            d[name] = path(d)

        for name, path in self._paths.items():
            if name in excludes:
                continue
            name = path.name or name
            if path.tmpstate:
                d.pop(name)
        return d
