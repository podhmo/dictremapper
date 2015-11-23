# -*- coding:utf-8 -*-
from collections import defaultdict, OrderedDict, namedtuple
import copy


Frame = namedtuple("Frame", "name remapper excludes")


class Counter(object):
    def __init__(self, i=0):
        self.i = i

    def __call__(self):
        self.i += 1
        return self.i

count = Counter(0)


def maybe_list(xs, delimiter="."):
    if hasattr(xs, "split"):
        return xs.split(delimiter)
    return xs


marker = object()


class Composed(object):
    aggregate = False

    def __init__(self, xs, callback=sum, tmpstate=False):
        self.xs = xs
        self._i = count()
        self.callback = callback
        self.tmpstate = tmpstate

    def __call__(self, stack, mapper, data):
        ys = [x(stack, mapper, data) for x in self.xs]
        return self.callback(*ys)


class Path(object):
    aggregate = False

    def __init__(self, keys, default=marker, callback=None, tmpstate=False):
        self._i = count()
        self.default = default
        self.keys = maybe_list(keys)
        self.callback = callback
        self.tmpstate = tmpstate

    def __call__(self, stack, mapper, data):
        try:
            for k in self.keys:
                data = data[k]
            if self.callback is not None:
                if hasattr(self.callback, "many"):  # remapper
                    data = self.callback(data, stack=stack)
                else:
                    data = self.callback(data)
            return data
        except KeyError:
            if self.default is marker:
                raise KeyError("{k} is not in {v}".format(k=k, v=data))
            return self.default


class ChangeOrder(object):
    def __init__(self, path):
        self._i = count()
        self.path = path

    def __call__(self, stack, mapper, data):
        return self.path(stack, mapper, data)

    def __getattr__(self, k):
        return getattr(self.path, k)

EMPTY = {"": set()}


class ExcludeSet(object):
    def __init__(self, excludes):
        if excludes is None:
            self.data = EMPTY
        else:
            self.data = self.transform(excludes)
        self.cache = {}

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
        cached_value = self.cache.get(id(d))
        if cached_value is None:
            cached_value = self.cache[id(d)] = merge_dict(copy.deepcopy(self.data), d)
        return cached_value

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

    def __call__(self, data, stack=None):
        stack = stack or []
        if self.many:
            return self.as_list(data, stack)
        else:
            return self.as_dict(data, stack)

    def as_list(self, dataset, stack):
        return [self.as_dict(data, stack) for data in dataset]

    def get_current_excludes_dict(self, stack):
        if not stack:
            return self.excludes
        return self.excludes.merge(stack[-1].excludes)

    def as_dict(self, data, stack):
        d = self.dict()
        dummy = object()
        lazies = []
        excludes_dict = self.get_current_excludes_dict(stack)
        excludes = excludes_dict.get("", [])

        for name, path in self._paths.items():
            if name in excludes:
                continue
            elif path.aggregate:
                lazies.append((name, path))
                d[name] = dummy
            else:
                stack.append(Frame(name=name, remapper=self, excludes=excludes_dict.get(name, EMPTY)))
                d[name] = path(stack, self, data)
                stack.pop()
        for name, path in lazies:
            d[name] = path(d)

        for name, path in self._paths.items():
            if name in excludes:
                continue
            elif path.tmpstate:
                d.pop(name)
        return d
