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

support nested structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

excludes option of each layer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
