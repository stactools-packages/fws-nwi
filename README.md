# stactools-fws-nwi

[![PyPI](https://img.shields.io/pypi/v/stactools-fws-nwi)](https://pypi.org/project/stactools-fws-nwi/)

- Name: fws-nwi
- Package: `stactools.fws_nwi`
- [stactools-fws-nwi on PyPI](https://pypi.org/project/stactools-fws-nwi/)
- Owner: @m-mohr
- Dataset homepage:
  - <https://www.fws.gov/program/national-wetlands-inventory>
- STAC extensions used:
  - [FWS NWI](https://github.com/stac-extensions/usfws-nwi/)
  - [processing](https://github.com/stac-extensions/processing/)
  - [proj](https://github.com/stac-extensions/projection/)
  - [table](https://github.com/stac-extensions/table/) (for geoparquet only)
- Extra fields:
  - See the [FWS NWI Extension Specification](https://github.com/stac-extensions/usfws-nwi/) for details.

stactools package for the National Wetlands Inventory (NWI) product
provided by the U.S. Fish and Wildlife Service (FWS).

The Wetlands Data Layer is the product of over 45 years of work by the National
Wetlands Inventory (NWI) and its collaborators and currently contains more than
35 million wetland and deepwater features. This dataset, covering the conterminous 
United States, Hawaii, Puerto Rico, the Virgin Islands, Guam, the major Northern 
Mariana Islands and Alaska, continues to grow at a rate of 50 to 100 million acres 
annually as data are updated. The data layer is updated twice a year and these 
changes are reflected on the mapper and in the data downloads.

## STAC Examples

- [Collection](examples/collection.json)
- [Item](examples/item.json)
- [Browse the example in human-readable form](https://radiantearth.github.io/stac-browser/#/external/raw.githubusercontent.com/stactools-packages/fws-nwi/main/examples/collection.json)

## Installation

```shell
pip install stactools-fws-nwi
```

## Command-line Usage

Use `stac fws-nwi --help` to see all subcommands and options.

### Collection

Create a collection:

```shell
stac fws-nwi create-collection collection.json
```

Get information about all options for collection creation:

```shell
stac fws-nwi create-collection --help
```

### Item

Create an item:

```shell
stac fws-nwi create-item /path/to/source/file.zip item.json --collection collection.json
```

Get information about all options for item creation:

```shell
stac fws-nwi create-item --help
```

## Contributing

We use [pre-commit](https://pre-commit.com/) to check any changes.
To set up your development environment:

```shell
pip install -e .
pip install -r requirements-dev.txt
pre-commit install
```

To check all files:

```shell
pre-commit run --all-files
```

To run the tests:

```shell
pytest -vv
```

### Tests



Due to the large file sizes, only the data files for the state of DC has been added to the repository so that 
we can ensure the basic functionality of the item creation is working.
To run the full suite of tests, please download more shapefiles from the
[U.S. Fish & Wildlife Service](https://www.fws.gov/node/264847), e.g. for South Dakota.
After download, please **don't** extract the zip files. Instead, please the ZIP files files in 
the `tests/data-files/external` folder.

Thus, the CI doesn't runs the tests for item generation on DC only due to the lack of more data files in the repository.
Please ensure you've tested the changes against more data files locally!

