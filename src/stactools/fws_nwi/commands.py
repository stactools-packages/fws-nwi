import logging
import os
import pathlib
from typing import List, Optional

import click
import requests
from click import Command, Group, Path
from pystac import Collection
from tqdm import tqdm

from stactools.fws_nwi import stac
from stactools.fws_nwi.states import States

logger = logging.getLogger(__name__)


def create_fwsnwi_command(cli: Group) -> Command:
    """Creates the stactools-fws-nwi command line utility."""

    @cli.group(
        "fws-nwi",
        short_help=("Commands for working with stactools-fws-nwi"),
    )
    def fwsnwi() -> None:
        pass

    @fwsnwi.command(
        "create-collection",
        short_help="Creates a STAC collection",
    )
    @click.argument("destination")
    @click.option(
        "--id",
        default="fws-nwi",
        help="A custom collection ID, defaults to 'fws-nwi'",
    )
    @click.option(
        "--thumbnail",
        default="",
        help="URL for the PNG or JPEG collection thumbnail asset (none if empty)",
    )
    @click.option(
        "--nogeoparquet",
        default=False,
        help="Does not include the geoparquet-related metadata in the collection if set to `TRUE`.",
    )
    @click.option(
        "--noshp",
        default=False,
        help="Does not include the shapefile-related metadata in the collection if set to `TRUE`.",
    )
    @click.option(
        "--start_time",
        default=None,
        help="The start timestamp for the temporal extent, defaults to now. "
        "Timestamps consist of a date and time in UTC and must be follow RFC 3339, section 5.6.",
    )
    def create_collection_command(
        destination: str,
        id: str = "fws-nwi",
        thumbnail: str = "",
        nogeoparquet: bool = False,
        noshp: bool = False,
        start_time: Optional[str] = None,
    ) -> None:
        """Creates a STAC Collection

        Args:
            destination (str): An HREF for the Collection JSON
        """
        collection = stac.create_collection(
            id, thumbnail, nogeoparquet, noshp, start_time
        )
        collection.set_self_href(destination)

        collection.save_object()

        return None

    @fwsnwi.command("create-item", short_help="Create a STAC item")
    @click.argument("source")
    @click.argument("destination")
    @click.option(
        "--collection",
        default="",
        help="An HREF to the Collection JSON. "
        "This adds the collection details to the item, but doesn't add the item to the collection.",
    )
    @click.option(
        "--nogeoparquet",
        default=False,
        help="Does not create geoparquet files for the given shapefile if set to `TRUE`.",
    )
    @click.option(
        "--noshp",
        default=False,
        help="Does not include the shapefile in the created metadata if set to `TRUE`.",
    )
    @click.option(
        "--datetime",
        default="",
        help="The datetime for the Item, defaults to now. "
        "Datetimes consist of a date and time in UTC and must be follow RFC 3339, section 5.6.",
    )
    @click.option(
        "--chunk_size",
        default=5000,
        help="The number of rows to read from the shapefile and to write to the geoparquet file "
        "per chunk. Only applies if --nogeoparquet is False. Defaults to 5000.",
    )
    def create_item_command(
        source: str,
        destination: str,
        collection: str = "",
        nogeoparquet: bool = False,
        noshp: bool = False,
        datetime: str = "",
        chunk_size: int = 5000,
    ) -> None:
        """Creates a STAC Item

        Args:
            source (str): HREF of the Asset associated with the Item
            destination (str): An HREF for the STAC Item
        """
        if chunk_size < 1:
            raise Exception("Chunk size must be > 0")

        stac_collection = None
        if len(collection) > 0:
            stac_collection = Collection.from_file(collection)

        item = stac.create_item(
            source, stac_collection, nogeoparquet, noshp, datetime, chunk_size
        )
        item.save_object(dest_href=destination)

        return None

    @fwsnwi.command("download", short_help="Download zipped shapefiles")
    @click.argument("codes", nargs=-1)
    @click.argument("destination", nargs=1)
    def download(codes: List[str], destination: Path) -> None:
        """Downloads some FWI zip files to the destination directory.

        If no codes are provided, downloads them all. This will take a while.
        """
        if not codes:
            codes = States.codes()
        os.makedirs(str(destination), exist_ok=True)
        for code in codes:
            url = f"https://www.fws.gov/wetlands/Data/State-Downloads/{code}_shapefile_wetlands.zip"
            path = pathlib.Path(str(destination)) / os.path.basename(url)
            response = requests.get(url, stream=True)
            with tqdm.wrapattr(
                open(path, "wb"),
                "write",
                miniters=1,
                desc=url.split("/")[-1],
                total=int(response.headers.get("content-length", 0)),
            ) as fout:
                for chunk in response.iter_content(chunk_size=4096):
                    fout.write(chunk)

    return fwsnwi
