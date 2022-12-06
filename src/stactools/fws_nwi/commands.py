import logging
import os
import pathlib
from typing import List, Optional

import click
import requests
from click import Command, Group, Path
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
        raise NotImplementedError

    @fwsnwi.command("create-item", short_help="Create a STAC item")
    @click.argument("source")
    @click.argument("destination")
    @click.option(
        "--create-geoparquet/--no-create-geoparquet",
        default=False,
        help="Create geoparquet assets alongside the item",
        show_default=True,
    )
    @click.option(
        "--make-asset-hrefs-relative/--no-make-asset-hrefs-relative",
        default=False,
        help="Make asset hrefs relative",
        show_default=True,
    )
    @click.option(
        "--include-self-link/--no-include-self-link",
        default=False,
        help="Include a self link",
        show_default=True,
    )
    def create_item_command(
        source: Path,
        destination: Path,
        create_geoparquet: bool,
        make_asset_hrefs_relative: bool,
        include_self_link: bool,
    ) -> None:
        """Creates a STAC Item

        Args:
            source (str): HREF of the Asset associated with the Item
            destination (str): An HREF for the STAC Item
        """
        destination_path = pathlib.Path(str(destination))
        if create_geoparquet:
            geoparquet_directory = destination_path.parent
        else:
            geoparquet_directory = None
        item = stac.create_item(
            pathlib.Path(str(source)), geoparquet_directory=geoparquet_directory
        )
        item.set_self_href(str(destination_path.absolute()))
        item.make_asset_hrefs_absolute()
        if make_asset_hrefs_relative:
            item.make_asset_hrefs_relative()
        item.save_object(include_self_link=include_self_link)
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
