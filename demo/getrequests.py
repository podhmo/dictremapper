# -*- coding:utf-8 -*-
import requests
import json
from dictremapper import Remapper, Path


class SummaryRemapper(Remapper):
    fullname = Path("full_name")
    url = Path("html_url")
    description = Path("description")

url = "https://api.github.com/repos/podhmo/dictremapper"
data = requests.get(url).json()
data = SummaryRemapper()(data)
print(json.dumps(data, indent=2))

# output
{
  "fullname": "podhmo/dictremapper",
  "url": "https://github.com/podhmo/dictremapper",
  "description": "remapping dict"
}
