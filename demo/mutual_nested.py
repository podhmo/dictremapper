# -*- coding:utf-8 -*-
import json
from dictremapper import Remapper, Path, LazyMapperCallable


class AuthorMapper(Remapper):
    name = Path("name")
    books = Path("books", callback=LazyMapperCallable("__main__.BookMapper", many=True, excludes=('author', )))


class BookMapper(Remapper):
    title = Path("title")
    author = Path("author", callback=LazyMapperCallable("__main__.AuthorMapper", excludes=("books", )))


def pp(data):
    print(json.dumps(data, indent=2))


d = {
    "id": 124,
    "title": "As I Lay Dying",
    "author": {
        "id": 8,
        "name": "William Faulkner"
    }
}
pp(BookMapper()(d))

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
pp(AuthorMapper()(d2))
