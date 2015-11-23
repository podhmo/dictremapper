dictremapper
========================================

dictremapper is remapping dict library

- ordered (important)
- support inheritance (of mapper)
- support nested structure
- (excludes option of each layer)

simple example
----------------------------------------

.. code-block:: python

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

output ::

    {
      "fullname": "podhmo/dictremapper",
      "url": "https://github.com/podhmo/dictremapper",
      "description": "remapping dict"
    }


support inheritance (of mapper)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

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

output ::

  {
    "url": "https://github.com/podhmo/dictremapper",
    "fullname": "podhmo/dictremapper",
    "description": "remapping dict",
    "star": 0
  }

If you want to change order. `ChangeOrder` is helpful, maybe.

.. code-block:: python

    from dictremapper import ChangeOrder


    class SummaryRemapper2(URLRemapper, DescriptionRemapper):
        url = ChangeOrder(URLRemapper.url)
        description = ChangeOrder(DescriptionRemapper.description)
        star = Path("stargazers_count")

    remapped = SummaryRemapper2()(data)
    print(json.dumps(remapped, indent=2))

output ::

  {
    "fullname": "podhmo/dictremapper",
    "url": "https://github.com/podhmo/dictremapper",
    "description": "remapping dict",
    "star": 0
  }


support nested structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block :: python

    class MyMapper3(Remapper):
        body = Path("body", callback=MyMapper())
        children = Path("children", callback=MyMapper2(many=True))


excludes option of each layer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block :: python

    class MyMapper3(Remapper):
        body = Path("body", callback=MyMapper())
        children = Path("children", callback=MyMapper2(many=True, excludes=["object.name", "object.age", "id"]))

   MyMapper3(excludes=["children.object.description", "body"])(d)
