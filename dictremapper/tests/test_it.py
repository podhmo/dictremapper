# -*- coding:utf-8 -*-
import unittest


class Tests(unittest.TestCase):
    def _getTargetClass(self):
        from dictremapper import Remapper
        return Remapper

    def _getPath(self, *args, **kwargs):
        from dictremapper import Path
        return Path(*args, **kwargs)

    def test_inherited(self):
        class URL(self._getTargetClass()):
            url = self._getPath("html.html_url")

        class MyMapper(URL):
            name = self._getPath("full_name")
            star = self._getPath("stargazers_count", default=0, callback=int)

        d = {"html": {"html_url": "xxxx"}, "full_name": "yyyy"}
        mapper = MyMapper()

        result = mapper(d)
        self.assertEqual(result, {"name": "yyyy", "url": "xxxx", "star": 0})
        self.assertEqual(list(result.keys()), ["url", "name", "star"])

    def test_inherited__change_order(self):
        from dictremapper import ChangeOrder

        class URL(self._getTargetClass()):
            url = self._getPath("html.html_url")

        class MyMapper(URL):
            name = self._getPath("full_name")
            url = ChangeOrder(URL.url)
            star = self._getPath("stargazers_count", default=0, callback=int)

        d = {"html": {"html_url": "xxxx"}, "full_name": "yyyy"}
        mapper = MyMapper()

        result = mapper(d)
        self.assertEqual(result, {"name": "yyyy", "url": "xxxx", "star": 0})
        self.assertEqual(list(result.keys()), ["name", "url", "star"])

    def test_nested(self):
        class MyMapper(self._getTargetClass()):
            name = self._getPath("full_name")
            url = self._getPath("html.html_url")
            star = self._getPath("stargazers_count", default=0, callback=int)

        class MyMapper2(self._getTargetClass()):
            body = self._getPath("main", callback=MyMapper())

        d = {"html": {"html_url": "xxxx"}, "full_name": "yyyy"}
        result = MyMapper2()({"main": d})
        self.assertEqual(result, {"body": {"name": "yyyy", "url": "xxxx", "star": 0}})

    def test_it__many_option(self):
        from collections import OrderedDict

        class MyMapper(self._getTargetClass()):
            name = self._getPath("full_name")
            url = self._getPath("html_url")

        d = [
            {"html_url": "xxxx1", "full_name": "yyyy1"},
            {"html_url": "xxxx2", "full_name": "yyyy2"},
        ]
        result = MyMapper(many=True)(d)
        self.assertEqual(result, [
            OrderedDict([("name", "yyyy1"), ("url", "xxxx1")]),
            OrderedDict([("name", "yyyy2"), ("url", "xxxx2")]),
        ])

    def test_nested__many_option(self):
        from collections import OrderedDict

        class MyMapper(self._getTargetClass()):
            name = self._getPath("full_name")
            url = self._getPath("html_url")

        class MyMapper2(self._getTargetClass()):
            packages = self._getPath("packages", callback=MyMapper(many=True))

        d = {
            "packages": [
                {"html_url": "xxxx1", "full_name": "yyyy1"},
                {"html_url": "xxxx2", "full_name": "yyyy2"},
            ]
        }
        result = MyMapper2()(d)
        self.assertEqual(result, OrderedDict([("packages", [
            OrderedDict([("name", "yyyy1"), ("url", "xxxx1")]),
            OrderedDict([("name", "yyyy2"), ("url", "xxxx2")]),
        ])]))

    def test_composed(self):
        from dictremapper import Composed

        class MyMapper(self._getTargetClass()):
            fullname = Composed(
                [self._getPath("first_name"), self._getPath("last_name")],
                callback=lambda x, y: "{} {}".format(x, y)
            )

        result = MyMapper()({"first_name": "foo", "last_name": "bar"})
        self.assertEqual(result, {"fullname": "foo bar"})
