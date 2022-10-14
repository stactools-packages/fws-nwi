import glob
import logging
import os
import tempfile
import zipfile as ziplib
from datetime import datetime, timezone
from typing import List, Optional

import pyproj
import shapefile
from dateutil.parser import isoparse
from pystac import (
    Asset,
    CatalogType,
    Collection,
    Extent,
    Item,
    Link,
    MediaType,
    SpatialExtent,
    Summaries,
    TemporalExtent,
)
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.table import TableExtension
from shapely.geometry import Polygon, shape
from shapely.ops import transform

from . import constants, parquet, shp, states

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
            "fws_nwi:state": states.State.names(),
            "fws_nwi:state_code": states.State.codes(),
            "proj:epsg": [constants.CRS],
        },
        # Up the maxcount, otherwise the state arrays will be omitted from output
        maxcount=len(states.State) + 1,
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

    item_assets = {}

    if not nogeoparquet:
        TableExtension.ext(collection, add_if_missing=True)
        asset = parquet.create_asset_metadata(constants.PARQUET_TITLE_WETLANDS)
        item_assets[constants.PARQUET_KEY_WETLANDS] = AssetDefinition(asset)

    if not noshp:
        TableExtension.ext(collection, add_if_missing=True)
        asset = shp.create_asset_metadata()
        item_assets[constants.SHP_KEY] = AssetDefinition(asset)

    item_assets_attrs = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets_attrs.item_assets = item_assets

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

    if ext.lower() != ".zip":
        raise Exception(f"Please specify a ZIP file, got {ext}")
    if code not in states.State.codes():
        raise Exception(f"Invalid state code in file name, got {code}")
    else:
        state = states.State[code]
    if ftype != "shapefile":
        raise Exception(
            f"Please specify a ZIP file containing a shapefile, got {ftype}"
        )
    if domain != "wetlands":
        raise Exception(f"Expected wetlands, got {domain}")

    with tempfile.TemporaryDirectory() as tempdir, ziplib.ZipFile(
        asset_href, "r"
    ) as zipfile:
        zipfile.extractall(tempdir)
        folder = os.path.join(tempdir, filename)
        shapefiles = list_shapefiles(folder)

        data_filename = f"{code}_Wetlands.shp"
        data_file = os.path.join(folder, data_filename)
        if data_filename not in shapefiles:
            raise Exception(f"Data file '{data_file}' not available")

        state_border_filename = f"{state}.shp"
        state_border_file = os.path.join(folder, state_border_filename)
        if state_border_filename in shapefiles:
            native_geom = load_geometry(state_border_file)
        else:
            raise Exception(f"Geometry file '{state_border_file}' not available")

        meta_filename = f"{code}_Wetlands_Project_Metadata.shp"
        meta_file = os.path.join(folder, meta_filename)
        if meta_filename in shapefiles:
            lineage = load_lineage(meta_file)
        else:
            lineage = None

        properties = {
            "title": f"{state} Wetlands",
            "fws_nwi:state": state,
            "fws_nwi:state_code": code,
            "processing:lineage": lineage,
        }

        # Time must be in UTC
        if len(item_datetime_str) == 0:
            item_datetime = datetime.now(tz=timezone.utc)
        else:
            item_datetime = isoparse(item_datetime_str)

        wgs84_geom = toWGS84(native_geom)

        item = Item(
            stac_extensions=[
                constants.NWI_EXTENSION,
                constants.PROCESSING_EXTENSION,
            ],
            id=filename,
            properties=properties,
            geometry=wgs84_geom.__geo_interface__,
            bbox=wgs84_geom.bounds,
            datetime=item_datetime,
            collection=collection,
        )

        # Add links
        hist_filename = f"{code}_Wetlands_Historic_Map_Info.shp"
        hist_file = os.path.join(folder, hist_filename)
        if hist_filename in shapefiles:
            add_archive_links(item, hist_file)

        # Projection
        proj_attrs = ProjectionExtension.ext(item, add_if_missing=True)
        proj_attrs.epsg = constants.CRS
        proj_attrs.bbox = native_geom.bounds
        proj_attrs.geometry = native_geom.__geo_interface__

        with shapefile.Reader(data_file) as reader:
            # Assets
            if not nogeoparquet:
                # target_folder = os.path.dirname(asset_href)
                # asset = parquet.convert(reader, target_folder)
                asset_dict = parquet.create_asset_metadata(
                    constants.PARQUET_TITLE_WETLANDS, data_file
                )
                asset = Asset.from_dict(asset_dict)
                item.add_asset(constants.PARQUET_KEY_WETLANDS, asset)
                table = TableExtension.ext(asset, add_if_missing=True)
                table.row_count = len(reader.records())

            if not noshp:
                asset_dict = shp.create_asset_metadata(asset_href)
                asset = Asset.from_dict(asset_dict)
                item.add_asset(constants.SHP_KEY, asset)

        return item


def load_lineage(path: str) -> Optional[str]:
    with shapefile.Reader(path) as shp:
        records = shp.records()
        if len(records) > 0:
            text = "### Projects\n"
            for record in records:
                name = record["PROJECT_NA"]
                link = record["SUPPMAPINF"]
                if link is not None and len(link) > 0 and link != "None":
                    name = f"[{name}]({link})"

                status = record["STATUS"]
                year = record["IMAGE_YR"]
                cat = record["DATA_CAT"]
                heading = f"**{name}** ({status}, {year}, {cat})"

                src = record["DATA_SOURC"]
                if src is not None and len(src) > 0:
                    heading = heading + f" with data from *{src}*"

                text = text + f"\n* {heading}"

                comment = record["COMMENTS"]
                if comment is not None and len(comment) > 0:
                    text = text + f"\n    * {comment}"
            return text
        else:
            return None


def add_archive_links(item: Item, path: str) -> None:
    with shapefile.Reader(path) as shp:
        records = shp.records()
        for record in records:
            title = record["PDF_NAME"]
            if title.lower().endswith(".pdf"):
                title = title[0:-4]

            link = Link(
                target=record["PDF_HYPERL"],
                media_type="application/pdf",
                title=title,
                rel="archives",
            )
            item.links.append(link)


def load_geometry(path: str) -> Polygon:
    with shapefile.Reader(path) as shp:
        if len(shp) != 1:
            raise Exception("Geometry file should only contain a single shape")
        return shape(shp.shape(0).__geo_interface__)


def toWGS84(geom: Polygon) -> Polygon:
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
