#!/usr/bin/env python

from pathlib import Path
from tempfile import TemporaryDirectory

import stactools.core.copy
from pystac import CatalogType

from stactools.fws_nwi import stac

root = Path(__file__).parents[1]
examples = root / "examples"
zipfile = root / "tests" / "data-files" / "DC_shapefile_wetlands.zip"

collection = stac.create_collection()
with TemporaryDirectory() as temporary_directory:
    item = stac.create_item(zipfile, Path(temporary_directory))
    collection.add_item(item)
    collection.normalize_hrefs(str(examples))
    stactools.core.copy.move_all_assets(
        collection, make_hrefs_relative=True, copy=True, ignore_conflicts=True
    )
collection.save(CatalogType.SELF_CONTAINED)
