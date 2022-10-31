import glob
import os.path
import unittest
import warnings
from datetime import datetime

# from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dateutil.parser import isoparse
from pystac import Collection

from stactools.fws_nwi import stac

from . import context

THUMBNAIL = "https://example.com/thumb.png"

TEST_COLLECTIONS: List[Dict[str, Any]] = [
    {
        "id": "my-id",
        "thumbnail": THUMBNAIL,
        "start_time": "2017-01-01T00:00:00.000Z",
    },
    {
        "nogeoparquet": True,
    },
    {
        "noshp": True,
    },
]

TEST_ITEMS: List[Dict[str, Any]] = [
    {
        "asset_href": context.DC_FILE,
        "collection": os.path.join(context.SOURCE_FOLDER, "collection.json"),
        "item_datetime_str": "2017-01-01T00:00:00.000Z",
        "chunk_size": 500,
    },
    {
        "asset_href": context.DC_FILE,
        "nogeoparquet": True,
    },
    {
        "asset_href": context.DC_FILE,
        "noshp": True,
    },
]

BASE_TEST_COUNT = len(TEST_ITEMS)

files = glob.glob(f"{context.EXTERNAL_FOLDER}/*.zip")
for file in files:
    TEST_ITEMS.append({"asset_href": file})


class StacTest(unittest.TestCase):
    def test_create_collection(self) -> None:
        for test_data in TEST_COLLECTIONS:
            with self.subTest(test_data=test_data):
                id: str = test_data["id"] if "id" in test_data else "fws-nwi"
                nogeoparquet: bool = (
                    test_data["nogeoparquet"] if "nogeoparquet" in test_data else False
                )
                noshp: bool = test_data["noshp"] if "noshp" in test_data else False

                collection = stac.create_collection(**test_data)
                collection.set_self_href("")
                collection.validate()
                collection_dict = collection.to_dict()

                self.assertEqual(collection.id, id)
                self.assertEqual(collection.title, context.TITLE)
                self.assertEqual(collection.license, "proprietary")
                # self.assertEqual(len(collection.providers), 1)

                self.assertTrue("summaries" in collection_dict)
                summaries = collection_dict["summaries"]
                self.assertIn("fws_nwi:state", summaries)
                self.assertIn("fws_nwi:state_code", summaries)
                self.assertTrue(
                    len(summaries["fws_nwi:state"])
                    == len(summaries["fws_nwi:state_code"])
                )
                self.assertIn("fws_nwi:content", summaries)
                self.assertEqual(summaries["fws_nwi:content"], context.CONTENT)

                self.assertIsNotNone(collection.keywords)
                if collection.keywords is not None:
                    if not noshp:
                        self.assertIn("Shapefile", collection.keywords)
                        self.assertIn("SHP", collection.keywords)
                    if not nogeoparquet:
                        self.assertIn("GeoParquet", collection.keywords)

    def test_create_item(self) -> None:
        if len(TEST_ITEMS) == BASE_TEST_COUNT:
            warnings.warn("No additional data files for tests found.")
        for test_data in TEST_ITEMS:
            with self.subTest(test_data=test_data):
                src_data_file: str = test_data["asset_href"]
                id: str = os.path.splitext(os.path.basename(src_data_file))[0]
                # nogeoparquet = (
                #     test_data["nogeoparquet"] if "nogeoparquet" in test_data else False
                # )
                # noshp: bool = test_data["noshp"] if "noshp" in test_data else False
                dt: Optional[datetime] = (
                    isoparse(test_data["item_datetime_str"])
                    if "item_datetime_str" in test_data
                    else None
                )

                collection: Optional[Collection] = None
                if "collection" in test_data:
                    collection = Collection.from_file(test_data["collection"])
                test_data["collection"] = collection

                item = stac.create_item(**test_data)
                item.validate()

                self.assertIsNotNone(item)
                self.assertEqual(item.id, id)
                # self.assertEqual(item.bbox, context.BBOX)
                # self.assertEqual(item.geometry, context.GEOMETRY)
                if collection is not None:
                    self.assertEqual(item.collection_id, collection.id)
                else:
                    self.assertIsNone(item.collection_id)

                if dt is None:
                    self.assertIsNotNone(item.datetime)
                else:
                    self.assertEqual(item.datetime, dt)
