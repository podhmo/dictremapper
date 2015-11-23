# -*- coding:utf-8 -*-
from collections import defaultdict, OrderedDict


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

    def __call__(self, mapper, data):
        ys = [x(mapper, data) for x in self.xs]
        return self.callback(*ys)


class Path(object):
    aggregate = False

    def __init__(self, keys, default=marker, callback=None, tmpstate=False):
        self._i = count()
        self.default = default
        self.keys = maybe_list(keys)
        self.callback = callback
        self.tmpstate = tmpstate

    def __call__(self, mapper, data):
        try:
            for k in self.keys:
                data = data[k]
            if self.callback is not None:
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

    def __call__(self, mapper, data):
        return self.path(mapper, data)

    def __getattr__(self, k):
        return getattr(self.path, k)


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

    def __init__(self, many=False):
        self.many = many

    def __call__(self, data):
        if self.many:
            return self.as_list(data)
        else:
            return self.as_dict(data)

    def as_list(self, dataset):
        return [self.as_dict(data) for data in dataset]

    def as_dict(self, data):
        d = self.dict()
        dummy = object()
        lazies = []

        for name, path in self._paths.items():
            if path.aggregate:
                lazies.append((name, path))
                d[name] = dummy
            else:
                d[name] = path(self, data)

        for name, path in lazies:
            d[name] = path(d)

        for name, path in self._paths.items():
            if path.tmpstate:
                d.pop(name)
        return d
