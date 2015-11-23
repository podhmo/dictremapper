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
            # todo: urlをここに
            star = self._getPath("stargazers_count", default=0, callback=int)

        d = {"html": {"html_url": "xxxx"}, "full_name": "yyyy"}
        mapper = MyMapper()

        result = mapper(d)
        self.assertEqual(result, {"name": "yyyy", "url": "xxxx", "star": 0})

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

    def test_composed(self):
        from dictremapper import Composed

        class MyMapper(self._getTargetClass()):
            fullname = Composed(
                [self._getPath("first_name"), self._getPath("last_name")],
                callback=lambda x, y: "{} {}".format(x, y)
            )

        result = MyMapper()({"first_name": "foo", "last_name": "bar"})
        self.assertEqual(result, {"fullname": "foo bar"})
