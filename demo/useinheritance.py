# -*- coding:utf-8 -*-
import requests
import json
from dictremapper import Remapper, Path


class URLRemapper(Remapper):
    url = Path("html_url")


class DescriptionRemapper(Remapper):
    fullname = Path("full_name")
    description = Path("description")


class SummaryRemapper(URLRemapper, DescriptionRemapper):
    star = Path("stargazers_count")

url = "https://api.github.com/repos/podhmo/dictremapper"
data = requests.get(url).json()
remapped = SummaryRemapper()(data)
print(json.dumps(remapped, indent=2))

# output
{
  "url": "https://github.com/podhmo/dictremapper",
  "fullname": "podhmo/dictremapper",
  "description": "remapping dict",
  "star": 0
}


# if you want to change order.
from dictremapper import ChangeOrder


class SummaryRemapper2(URLRemapper, DescriptionRemapper):
    url = ChangeOrder(URLRemapper.url)
    description = ChangeOrder(DescriptionRemapper.description)
    star = Path("stargazers_count")

remapped = SummaryRemapper2()(data)
print(json.dumps(remapped, indent=2))

# output
{
  "fullname": "podhmo/dictremapper",
  "url": "https://github.com/podhmo/dictremapper",
  "description": "remapping dict",
  "star": 0
}
