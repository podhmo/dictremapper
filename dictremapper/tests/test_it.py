# -*- coding:utf-8 -*-
import unittest


class Tests(unittest.TestCase):
    def _getTargetClass(self):
        from dictremapper import Remapper
        return Remapper

    def _getPath(self, *args, **kwargs):
        from dictremapper import Path
        return Path(*args, **kwargs)

    def test_freedom_naming(self):
        class MyMapper(self._getTargetClass()):
            name = self._getPath("name", name="@name-{myname}")

        d = {"name": "foo"}
        mapper = MyMapper()

        result = mapper(d)
        self.assertEqual(result, {"@name-{myname}": "foo"})

    def test_squashed(self):
        class MyMapper(self._getTargetClass()):
            nameset = self._getPath("repositories[].packages[].name")

        d = {
            "repositories": [
                {
                    "name": "abc",
                    "packages": [
                        {"name": "a"},
                        {"name": "b"},
                        {"name": "c"},
                    ]
                },
                {
                    "name": "xyz",
                    "packages": [
                        {"name": "x"},
                        {"name": "y"},
                    ]
                },
            ]
        }

        mapper = MyMapper()
        result = mapper(d)
        self.assertEqual(result["nameset"], [["a", "b", "c"], ["x", "y"]])

    def test_index_access_with_digit(self):
        class MyMapper(self._getTargetClass()):
            year = self._getPath("published_at.0")

        d = {"published_at": ["2000", "11", "12"]}
        mapper = MyMapper()

        result = mapper(d)
        self.assertEqual(result, {"year": "2000"})

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

    def test_exclude(self):
        class MyMapper(self._getTargetClass()):
            name = self._getPath("full_name")
            url = self._getPath("html_url")

        d = {"html_url": "xxxx", "full_name": "yyyy"}
        result = MyMapper(excludes=["url"])(d)
        self.assertEqual(result, {"name": "yyyy"})

    def test_nested__exclude(self):
        class MyMapper(self._getTargetClass()):
            name = self._getPath("full_name")
            url = self._getPath("html_url")

        class MyMapper2(self._getTargetClass()):
            body = self._getPath("main", callback=MyMapper())

        d = {"main": {"html_url": "xxxx", "full_name": "yyyy"}}
        result = MyMapper2(excludes=["body.url"])(d)
        self.assertEqual(result, {"body": {"name": "yyyy"}})

    def test_nested__exclude2(self):
        class MyMapper(self._getTargetClass()):
            name = self._getPath("full_name")
            url = self._getPath("html_url")

        class MyMapper2(self._getTargetClass()):
            body = self._getPath("main", callback=MyMapper(excludes=["url"]))

        d = {"main": {"html_url": "xxxx", "full_name": "yyyy"}}
        result = MyMapper2()(d)
        self.assertEqual(result, {"body": {"name": "yyyy"}})

    def test_nested__exclude3(self):
        class MyMapper(self._getTargetClass()):
            name = self._getPath("full_name")
            description = self._getPath("description")
            url = self._getPath("html_url")
            star = self._getPath("html_url", callback=int, default=0)

        class MyMapper2(self._getTargetClass()):
            body = self._getPath("main", callback=MyMapper(excludes=["star"]))

        class MyMapper3(self._getTargetClass()):
            toplevel = self._getPath("toplevel", callback=MyMapper2(excludes=["body.url"]))

        d = {"toplevel": {"main": {"html_url": "xxxx", "full_name": "yyyy", "star": "10", "description": "zzzzz"}}}
        result = MyMapper3(excludes=["toplevel.body.description"])(d)
        self.assertEqual(result, {"toplevel": {"body": {"name": "yyyy"}}})

    def test_nested__exclude4(self):
        class MyMapper(self._getTargetClass()):
            name = self._getPath("full_name")
            description = self._getPath("description")
            url = self._getPath("html_url")
            star = self._getPath("html_url", callback=int, default=0)

        class MyMapper2(self._getTargetClass()):
            packages = self._getPath("packages", callback=MyMapper(excludes=["star"], many=True))

        class MyMapper3(self._getTargetClass()):
            toplevel = self._getPath("toplevel", callback=MyMapper2(excludes=["packages.url"]))

        d = {"toplevel": {"packages": [
            {"html_url": "xxxx", "full_name": "yyyy", "star": "10", "description": "zzzzz"},
            {"html_url": "xxxx", "full_name": "yyyy", "star": "10", "description": "zzzzz"}
        ]}}
        result = MyMapper3(excludes=["toplevel.packages.description"])(d)
        self.assertEqual(result, {"toplevel": {"packages": [{"name": "yyyy"}, {"name": "yyyy"}]}})

    def test_composed(self):
        from dictremapper import Composed

        class MyMapper(self._getTargetClass()):
            fullname = Composed(
                [self._getPath("first_name"), self._getPath("last_name")],
                callback=lambda x, y: "{} {}".format(x, y)
            )

        result = MyMapper()({"first_name": "foo", "last_name": "bar"})
        self.assertEqual(result, {"fullname": "foo bar"})

    def test_shortcut(self):
        from dictremapper import Shortcut

        class MyMapper(self._getTargetClass()):
            name = self._getPath("Name")

        mapper = Shortcut(MyMapper(), "Main.Body.Packages[]")

        d = {
            "Main": {
                "Body": {
                    "Packages": [{"Name": "a"}, {"Name": "b"}]
                }
            }
        }

        result = mapper(d)
        self.assertEqual(result, [{"name": "a"}, {"name": "b"}])

    def test_lazy(self):
        from dictremapper import LazyMapperCallable

        # http://marshmallow.readthedocs.org/en/latest/nesting.html#two-way-nesting
        D = {}

        def loader(k):
            return D[k]

        class AuthorMapper(self._getTargetClass()):
            name = self._getPath("name")
            books = self._getPath("books", callback=LazyMapperCallable("BookMapper", many=True, excludes=('author', ), loader=loader))

        class BookMapper(self._getTargetClass()):
            title = self._getPath("title")
            author = self._getPath("author", callback=LazyMapperCallable("AuthorMapper", excludes=("books", ), loader=loader))

        D["AuthorMapper"] = AuthorMapper
        D["BookMapper"] = BookMapper

        d = {
            "id": 124,
            "title": "As I Lay Dying",
            "author": {
                "id": 8,
                "name": "William Faulkner"
            }
        }
        result = BookMapper()(d)
        self.assertEqual(result, {"title": "As I Lay Dying", "author": {"name": "William Faulkner"}})

        d2 = {
            "id": 8,
            "name": "William Faulkner",
            "books": [
                {
                    "id": 124,
                    "title": "As I Lay Dying"
                }
            ]
        }
        result2 = AuthorMapper()(d2)
        self.assertEqual(result2, {"name": "William Faulkner", "books": [{"title": "As I Lay Dying"}]})

    def test_nested_self(self):
        from dictremapper import Self

        class MyMapper(self._getTargetClass()):
            name = self._getPath("name")
            friends = self._getPath("friends", callback=Self(many=True))

        mapper = MyMapper()

        d = {
            "name": "Steve",
            "email": "steve@example.com",
            "friends": [
                {
                    "name": "Mike",
                    "email": "mike@example.com",
                    "friends": [],
                },
                {
                    "name": "Joe",
                    "email": "joe@example.com",
                    "friends": [],
                }
            ],
        }
        result = mapper(d)
        expected = {
            "name": "Steve",
            "friends": [
                {"name": "Mike", "friends": []},
                {"name": "Joe", "friends": []}
            ]
        }
        self.assertEqual(result, expected)
