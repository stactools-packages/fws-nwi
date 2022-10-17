import logging
import os
from typing import Any, Dict, List, Optional

import shapefile
from geopandas import GeoDataFrame, GeoSeries
from pystac import Asset
from shapely.geometry import shape

from . import constants, shp
from .content import Types, parse_name

logger = logging.getLogger(__name__)


IGNORE_COLS = ["DeletionFlag"]


def convert(
    files: List[str], content_type: Types, dest_folder: str
) -> Dict[str, Asset]:
    """
    Converts a shapefile reader to geoparquet files in the given folder.
    Returns a dict containing the three STAC Asset Objects for the geoparquet
    files.

    Args:
        dataset (shapefile.Reader): A shapefile reader
        dest_folder (str): The destination folder for the geoparquet files

    Returns:
        dict: Asset Objects
    """
    assets: Dict[str, Asset] = {}
    for file in files:
        key = parse_name(file, content_type).replace(" ", "_").lower()
        assets[key] = create_asset(file, content_type, dest_folder)

    return assets


def create_asset(src_file: str, content_type: Types, dest_folder: str) -> Asset:
    """
    Creates an asset object for a file with table properties.

    Args:
        file (str): The source file path
        type (Types): The content gategory of data to handle
        dest_folder (str): Folder to write the file to

    Returns:
        dict: Asset Object for the geoparquet file
    """
    filename = os.path.basename(src_file)[0:-4]  # filename without .shp
    dest_file = os.path.join(dest_folder, f"{filename}.parquet")

    with shapefile.Reader(src_file) as reader:
        # number of rows
        count = len(reader)

        # Convert shapes
        shapes = reader.shapes()
        geometries = [shape(s.__geo_interface__) for s in shapes]

        # Add geometry columns and data
        table_data = {
            constants.PARQUET_GEOMETRY_COL: GeoSeries(
                geometries, crs=constants.GEOM_CRS
            )
        }
        table_cols = [
            create_col(constants.PARQUET_GEOMETRY_COL, reader.shapeTypeName.lower())
        ]
        # Add all other columns, except for DeletionFlag
        for field in reader.fields:
            shp_col = field[0]
            if shp_col in IGNORE_COLS:
                continue

            col = shp_col.lower()
            table_data[col] = [reader.record(i)[shp_col] for i in range(0, count)]
            table_cols.append(create_col(col, shp.get_type(field)))

        # Create a geodataframe and store it as geoparquet file
        dataframe = GeoDataFrame(table_data)
        dataframe.to_parquet(dest_file, version="2.6")

        # Create asset metadata
        asset_dict = create_asset_metadata(content_type, dest_file)
        # Can't use table extension: https://github.com/stac-utils/pystac/issues/872
        asset_dict["table:primary_geometry"] = constants.PARQUET_GEOMETRY_COL
        asset_dict["table:columns"] = table_cols
        asset_dict["table:row_count"] = count
        asset = Asset.from_dict(asset_dict)

        return asset


def create_col(name: str, dtype: Optional[str] = None) -> Dict[str, str]:
    col = {"name": name}
    if dtype is not None:
        col["type"] = dtype
    return col


def create_asset_metadata(content_type: Types, href: str) -> Dict[str, Any]:
    """
    Creates a basic geoparquet asset dict with shared core properties.

    Args:
        title (str): A title for the asset
        href (str): The URL to the asset (optional)
        cols (List[Dict[str, Any]]): A list of columns (optional;
            compliant to table:columns)
        count: The number of rows in the asset (optional)

    Returns:
        dict: Basic Asset object
    """
    title = parse_name(href, content_type)
    asset: Dict[str, Any] = {
        "title": f"{title} GeoParquet file",
        "type": constants.PARQUET_MEDIA_TYPE,
        "roles": constants.PARQUET_ROLES + [content_type.value.lower()],
        "href": href,
    }

    return asset
