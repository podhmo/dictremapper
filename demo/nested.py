# -*- coding:utf-8 -*-
from dictremapper import Remapper, Path


class MyMapper(Remapper):
    pass


class MyMapper2(Remapper):
    pass


class MyMapper3(Remapper):
    body = Path("body", callback=MyMapper())
    children = Path("children", callback=MyMapper2(many=True))
