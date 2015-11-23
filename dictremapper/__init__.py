# -*- coding:utf-8 -*-
from collections import defaultdict, OrderedDict
import json


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
                raise
            return self.default


class Remapper(object):
    dict = OrderedDict

    def __new__(cls, *args, **kwargs):
        if "_paths" not in cls.__dict__:
            paths = defaultdict(list)
            for c in reversed(cls.mro()):
                for name, attr in c.__dict__.items():
                    if hasattr(attr, "_i"):  # path
                        paths[name].append(attr)
            cls._paths = OrderedDict((k, v[0]) for k, v in sorted(paths.items(), key=lambda vs: vs[1][0]._i))
        return super(Remapper, cls).__new__(cls, *args, **kwargs)

    def __call__(self, data):
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

if __name__ == "__main__":
    class URL(Remapper):
        url = Path("html.html_url")

    class MyMapper(URL):
        name = Path("full_name")
        # todo: urlをここに
        star = Path("stargazers_count", default=0, callback=int)

    class MyMapper2(Remapper):
        body = Path("main", callback=MyMapper())

    d = {"html": {"html_url": "xxxx"}, "full_name": "yyyy"}
    mapper = MyMapper()

    print(json.dumps(mapper(d), indent=2))
    print(json.dumps(MyMapper2()({"main": d}), indent=2))

    class MyMapper3(Remapper):
        fullname = Composed(
            [Path("first_name"), Path("last_name")],
            callback=lambda x, y: "{} {}".format(x, y)
        )

    d = {"first_name": "foo", "last_name": "bar"}
    print(json.dumps(MyMapper3()(d), indent=2))
