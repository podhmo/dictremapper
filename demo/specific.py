import json
from operator import itemgetter
import itertools
# https://gist.github.com/nvie/f304caf3b4f1ca4c3884

d = {
  "timestamp": 1412282459,
  "res": [
    {
      "group": "1",
      "catlist": [
        {
          "cat": "1",
          "start": "none",
          "stop": "none",
          "points": [
              {"point": "1", "start": "13.00", "stop": "13.35"},
              {"point": "2", "start": "11.00", "stop": "14.35"}
          ]
        }
      ]
    }
  ]
}


from dictremapper import Remapper, Path, Aggregate


class PointRemapper(Remapper):
    class _ResRemapper(Remapper):
        class _CatRemapper(Remapper):
            points = Path("points", callback=lambda v: list(sorted(v, key=itemgetter("start"))))
        catlist = Path("catlist", callback=_CatRemapper(many=True))

    res = Path("res", callback=_ResRemapper(many=True), tmpstate=True)

    @Aggregate
    def points(data):
        return [p for res in data["res"] for catlist in res["catlist"] for p in catlist["points"]]


class PointRemapper2(Remapper):
    def flatten_sort(v):
        flatten1 = itertools.chain.from_iterable
        return list(sorted(flatten1(flatten1(v)), key=itemgetter("start")))
    points = Path("res[].catlist[].points[]", callback=flatten_sort)


data = PointRemapper()(d)
print(json.dumps(data, indent=2))
data = PointRemapper2()(d)
print(json.dumps(data, indent=2))
