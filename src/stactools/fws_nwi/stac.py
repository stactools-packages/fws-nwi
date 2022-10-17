import glob
import logging
import os
import tempfile
import zipfile as ziplib
from datetime import datetime, timezone
from typing import List, Optional

import pyproj
from dateutil.parser import isoparse
from pystac import (
    Asset,
    CatalogType,
    Collection,
    Extent,
    Item,
    MediaType,
    SpatialExtent,
    Summaries,
    TemporalExtent,
)
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.table import TableExtension
from shapely.geometry import Polygon
from shapely.ops import transform

from . import constants, parquet, shp
from .content import Types, parse
from .states import States

logger = logging.getLogger(__name__)


def create_collection(
    id: str = "fws-nwi",
    thumbnail: str = "",
    nogeoparquet: bool = False,
    noshp: bool = False,
    start_time: Optional[str] = None,
) -> Collection:
    """Create a STAC Collection for NOAA MRMS QPE sub-products.

    Args:
        id (str): A custom collection ID, defaults to 'fws-nwi'
        thumbnail (str): URL for the PNG or JPEG collection thumbnail asset (none if empty)
        nogeoparquet (bool): If set to True, the collections does not include the
            geoparquet-related metadata
        noshp (bool): If set to True, the collections does not include the
            shapefile-related metadata
        start_time (str): The start timestamp for the temporal extent, default to now.
            Timestamps consist of a date and time in UTC and must follow RFC 3339, section 5.6.

    Returns:
        Collection: STAC Collection object
    """
    # Time must be in UTC
    if start_time is None:
        start_datetime = datetime.now(tz=timezone.utc)
    else:
        start_datetime = isoparse(start_time)

    extent = Extent(
        SpatialExtent(constants.COLLECTION_BBOXES),
        TemporalExtent([[start_datetime, None]]),
    )

    keywords = constants.KEYWORDS.copy()
    if not noshp:
        keywords.append("Shapefile")
        keywords.append("SHP")
    if not nogeoparquet:
        keywords.append("GeoParquet")

    summaries = Summaries(
        {
            "fws_nwi:state": States.names(),
            "fws_nwi:state_code": States.codes(),
            "fws_nwi:content": [t.lower() for t in Types.values()],
            "proj:epsg": [constants.CRS],
        },
        # Up the maxcount, otherwise the state arrays will be omitted from output
        maxcount=len(States) + 1,
    )

    collection = Collection(
        stac_extensions=[
            constants.NWI_EXTENSION,
            constants.PROJECTION_EXTENSION,
        ],
        id=id,
        title=constants.TITLE,
        description=constants.DESCRIPTION,
        keywords=keywords,
        license="proprietary",
        providers=[constants.PROVIDER_USFWS],
        extent=extent,
        summaries=summaries,
        catalog_type=CatalogType.RELATIVE_PUBLISHED,
    )

    collection.add_link(constants.LINK_LICENSE)
    collection.add_link(constants.LINK_LANDING_PAGE)
    collection.add_link(constants.LINK_FACT_SHEET)
    collection.add_link(constants.LINK_METADATA)

    if len(thumbnail) > 0:
        if thumbnail.endswith(".png"):
            media_type = MediaType.PNG
        else:
            media_type = MediaType.JPEG

        collection.add_asset(
            "thumbnail",
            Asset(
                href=thumbnail,
                title="Preview",
                roles=["thumbnail"],
                media_type=media_type,
            ),
        )

    return collection


def create_item(
    asset_href: str,
    collection: Optional[Collection] = None,
    nogeoparquet: bool = False,
    noshp: bool = False,
    item_datetime_str: str = "",
) -> Item:
    """Create a STAC Item

    This function should include logic to extract all relevant metadata from an
    asset, metadata asset, and/or a constants.py file.

    See `Item<https://pystac.readthedocs.io/en/latest/api.html#item>`_.

    Args:
        asset_href (str): The HREF pointing to an asset associated with the item
        collection (pystac.Collection): HREF to an existing collection
        nogeoparquet (bool): If set to True, no geoparquet file is generated for the Item
        noshp (bool): If set to True, the shapefile is not added to the Item
        item_datetime_str (str): The datetime for the Item, defaults to now.
            Datetimes consist of a date and time in UTC and must be follow RFC 3339, section 5.6.

    Returns:
        Item: STAC Item object
    """

    filename, ext = os.path.splitext(os.path.basename(asset_href))
    code, ftype, domain = filename.split("_")

    # Check filename for obvious issues
    if ext.lower() != ".zip":
        raise Exception(f"Please specify a ZIP file, got {ext}")
    if code not in States.codes():
        raise Exception(f"Invalid state code in file name, got {code}")
    else:
        state = States[code]

    if ftype != "shapefile":
        raise Exception(
            f"Please specify a ZIP file containing a shapefile, got {ftype}"
        )
    if domain != "wetlands":
        raise Exception(f"Expected wetlands, got {domain}")

    # Open and extract zip file
    with tempfile.TemporaryDirectory() as tempdir, ziplib.ZipFile(
        asset_href, "r"
    ) as zipfile:
        zipfile.extractall(tempdir)
        folder = os.path.join(tempdir, filename)
        # List all shapefiles that are present so that we can detect what's inside
        shapefiles = list_shapefiles(folder)

        # Detect data files because the file contet varies a lot
        content = parse(shapefiles, code, folder)
        content_flags = []
        for t in Types:
            if len(content[t].files) > 0:
                content_flags.append(t.value.lower())

        # Get / Compute geometries
        # Also specify a fallback shapefile in case a file with the state geometry
        # is missing. Then we'll derive a geometry from the other shapefiles.
        state_border_filename = state.replace(" ", "_") + ".shp"
        state_border_file = os.path.join(folder, state_border_filename)
        fallback_file = content[Types.WETLANDS].projects
        native_geom = shp.get_geometry(state_border_file, fallback_file)
        wgs84_geom = toWgs84(native_geom)

        # Prepare basic metadata for Item
        extensions = [constants.NWI_EXTENSION]
        properties = {
            "title": f"{state} Wetlands",
            "fws_nwi:state": state,
            "fws_nwi:state_code": code,
            "fws_nwi:content": content_flags,
        }

        # Build lineage
        lineage = "### Projects\n\n"
        lineage_title_length = len(lineage)
        for t in Types:
            lineage_file = content[t].projects
            if lineage_file is not None:
                lineage = lineage + shp.get_lineage(lineage_file, t)

        if len(lineage) > lineage_title_length:
            extensions.append(constants.PROCESSING_EXTENSION)
            properties["processing:lineage"] = lineage.strip()

        # Time must be in UTC
        if len(item_datetime_str) == 0:
            item_datetime = datetime.now(tz=timezone.utc)
        else:
            item_datetime = isoparse(item_datetime_str)

        # Create Item
        item = Item(
            stac_extensions=extensions,
            id=filename,
            properties=properties,
            geometry=wgs84_geom.__geo_interface__,
            bbox=wgs84_geom.bounds,
            datetime=item_datetime,
            collection=collection,
        )

        # Add archive links
        for t in Types:
            archive_file = content[t].archive
            if archive_file is not None:
                shp.add_archive_links(item, archive_file)

        # Projection
        proj_attrs = ProjectionExtension.ext(item, add_if_missing=True)
        proj_attrs.epsg = constants.CRS
        proj_attrs.bbox = native_geom.bounds
        proj_attrs.geometry = native_geom.__geo_interface__

        # Assets
        if not nogeoparquet:
            target_folder = os.path.dirname(asset_href)
            # Add the extension upfront so that we don't need to write spaghetti code
            # https://github.com/stac-utils/pystac/issues/793
            TableExtension.ext(item, add_if_missing=True)
            for t in Types:
                assets = parquet.convert(content[t].files, t, target_folder)
                for key in assets:
                    item.add_asset(key, assets[key])

        if not noshp:
            asset_dict = shp.create_asset_metadata(asset_href)
            item.add_asset(constants.SHP_KEY, Asset.from_dict(asset_dict))

        return item


def toWgs84(geom: Polygon) -> Polygon:
    source = pyproj.CRS(constants.GEOM_CRS)
    target = pyproj.CRS("EPSG:4326")

    project = pyproj.Transformer.from_crs(source, target, always_xy=True).transform
    return transform(project, geom)


def list_shapefiles(folder: str) -> List[str]:
    old_dir = os.getcwd()
    os.chdir(folder)
    shapefiles = glob.glob("*.shp")
    os.chdir(old_dir)
    return shapefiles
