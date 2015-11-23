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
        self.excludes = excludes or []

    def __call__(self, data, stack=None):
        stack = stack or []
        if self.many:
            return self.as_list(data, stack)
        else:
            return self.as_dict(data, stack)

    def as_list(self, dataset, stack):
        r = []
        for i, data in enumerate(dataset):
            stack.append(i)
            r.append(self.as_dict(data, stack))
            stack.pop()
        return r

    def as_dict(self, data, stack):
        d = self.dict()
        dummy = object()
        lazies = []
        for name, path in self._paths.items():
            if name in self.excludes:
                continue
            elif path.aggregate:
                lazies.append((name, path))
                d[name] = dummy
            else:
                stack.append(name)
                d[name] = path(stack, self, data)
                stack.pop()
        for name, path in lazies:
            d[name] = path(d)

        for name, path in self._paths.items():
            if name in self.excludes:
                continue
            elif path.tmpstate:
                d.pop(name)
        return d
