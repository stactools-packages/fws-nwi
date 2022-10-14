import logging

# import os
from typing import Any, Dict, Optional

from . import constants

# import shapefile
# from geopandas import GeoDataFrame, GeoSeries
# from shapely.geometry import Point


logger = logging.getLogger(__name__)


# def convert(dataset: shapefile.Reader, dest_folder: str) -> Dict[str, Dict[str, Any]]:
#     """
#     Converts a shapefile reader to geoparquet files in the given folder.
#     Returns a dict containing the three STAC Asset Objects for the geoparquet
#     files.

#     Args:
#         dataset (shapefile.Reader): A shapefile reader
#         dest_folder (str): The destination folder for the geoparquet files

#     Returns:
#         dict: Asset Objects
#     """
#     assets: Dict[str, Dict[str, Any]] = {}
#     assets[constants.PARQUET_KEY_WETLANDS] = create_wetlands(dataset, dest_folder)
#     return assets


# def create_wetlands(dataset: shapefile.Reader, dest_folder: str) -> Dict[str, Any]:
#     """
#     Creates geoparquet file from a shapefile reader for the wetlands.

#     Args:
#         dataset (shapefile.Reader): A shapefile reader

#     Returns:
#         dict: Asset Object for the geoparquet file
#     """
#     file = os.path.join(dest_folder, "wetlands.parquet")
#     cols = ["lat", "lon", "id", "time_offset", "energy", "parent_group_id"]
#     return create_asset(
#         dataset, file, "wetlands", cols, constants.PARQUET_TITLE_WETLANDS
#     )


# def create_asset(
#     dataset: shapefile.Reader, file: str, type: str, cols: List[str], title: str
# ) -> Dict[str, Any]:
#     """
#     Creates an asset object for a shapefile reader with some additional properties.

#     The type is the prefix of the columns in the shapefile and will be prefixed
#     to the cols (with a underscore in-between) when reading the shapefile.
#     The geoparquet file will use the cols, but without the prefix.

#     Args:
#         dataset (shapefile.Reader): A shapefile reader
#         file (str): The target file path
#         type (str): The group of data to write (one of: flash, event or group)
#         cols (List[str]): A list of columns to consider
#         title (str): A title for the asset

#     Returns:
#         dict: Asset Object for the geoparquet file
#     """
#     # create a list of points
#     geometries = []

#     for i in range(0, count):
#         geometries.append(Point(lon, lat))

#     # fill dict with all data in a columnar way
#     table_data = {
#         constants.PARQUET_GEOMETRY_COL: GeoSeries(geometries, crs=constants.GEOM_CRS)
#     }
#     table_cols = [{"name": constants.PARQUET_GEOMETRY_COL, "type": dataset.featureType}]
#     for col in cols:
#         if col == "lat" or col == "lon":
#             continue

#         var_name = f"{type}_{col}"
#         if var_name not in dataset.variables:
#             raise Exception(f"Variable '{var_name}' is missing")

#         variable = dataset.variables[var_name]
#         attrs = variable.ncattrs()
#         data = variable[...].tolist()
#         table_col = {
#             "name": col,
#             "type": str(variable.datatype),  # todo: check data type #11
#         }
#         if "long_name" in attrs:
#             table_col["description"] = variable.getncattr("long_name")

#         if "units" in attrs:
#             unit = variable.getncattr("units")
#             if unit == "percent":
#                 table_col["unit"] = "%"
#             else:
#                 table_col["unit"] = unit

#         table_data[col] = data
#         table_cols.append(table_col)

#     # Create a geodataframe and store it as geoparquet file
#     dataframe = GeoDataFrame(table_data)
#     dataframe.to_parquet(file, version="2.6")

#     # Create asset dict
#     return create_asset_metadata(title, file, table_cols, count)


def create_asset_metadata(title: str, href: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates a basic geoparquet asset dict with shared core properties (title,
    type, roles), properties for the table extension  and optionally an href.
    An href should be given for normal assets, but can be None for Item Asset
    Definitions.

    Args:
        title (str): A title for the asset
        href (str): The URL to the asset (optional)
        cols (List[Dict[str, Any]]): A list of columns (optional;
            compliant to table:columns)
        count: The number of rows in the asset (optional)

    Returns:
        dict: Basic Asset object
    """
    asset: Dict[str, Any] = {
        "title": title,
        "type": constants.PARQUET_MEDIA_TYPE,
        "roles": constants.PARQUET_ROLES,
        "table:primary_geometry": constants.PARQUET_GEOMETRY_COL,
    }
    if href is not None:
        asset["href"] = href
    return asset
