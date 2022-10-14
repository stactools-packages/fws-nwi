import logging
from typing import Optional

import click
from click import Command, Group
from pystac import Collection

from stactools.fws_nwi import stac

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
    def create_item_command(
        source: str,
        destination: str,
        collection: str = "",
        nogeoparquet: bool = False,
        noshp: bool = False,
    ) -> None:
        """Creates a STAC Item

        Args:
            source (str): HREF of the Asset associated with the Item
            destination (str): An HREF for the STAC Item
        """
        stac_collection = None
        if len(collection) > 0:
            stac_collection = Collection.from_file(collection)

        item = stac.create_item(source, stac_collection, nogeoparquet, noshp)
        item.save_object(dest_href=destination)

        return None

    return fwsnwi
