import json
import logging
import os
import struct
from typing import Any, Dict, List, Optional

import pyarrow as pa
import shapefile
import shapely
from pyarrow.parquet import ParquetWriter
from pyproj import CRS
from pystac import Asset
from pystac.extensions.projection import ProjectionExtension
from shapely.geometry import shape as to_geom

from . import constants, shp
from .content import Types, parse_name

logger = logging.getLogger(__name__)


IGNORE_COLS = ["DeletionFlag"]


def convert(
    files: List[str], content_type: Types, dest_folder: str, base_crs: CRS
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
        assets[key] = create_asset(file, content_type, dest_folder, base_crs)

    return assets


def create_asset(
    src_file: str, content_type: Types, dest_folder: str, base_crs: CRS
) -> Asset:
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

    logger.info(f"Opening {src_file} for conversion")

    # Read projection
    crs = shp.get_projection(src_file)

    # Read shapefile
    with shapefile.Reader(src_file) as reader:
        # number of rows
        count = len(reader)

        if reader.shapeTypeName.upper() != constants.PARQUET_GEOMETRY_TYPE.upper():
            raise Exception(
                (
                    f"Unexpected shapetype '{constants.PARQUET_GEOMETRY_TYPE}', "
                    f"got {reader.shapeTypeName}"
                )
            )

        # Get columns, except for ignored ones (DeletionFlag)
        stac_table_cols = [
            create_col(constants.PARQUET_GEOMETRY_COL, constants.PARQUET_GEOMETRY_TYPE)
        ]
        pa_cols = [pa.field(constants.PARQUET_GEOMETRY_COL, pa.binary())]
        for field in reader.fields:
            shp_col = field[0]
            if shp_col in IGNORE_COLS:
                continue

            col = shp_col.lower()

            dtype = shp.get_type(field)
            stac_table_cols.append(create_col(col, dtype))

            pa_dtype = get_pyarrow_type(dtype)
            pa_cols.append(pa.field(col, pa_dtype))

        col_range = range(len(pa_cols))

        # Stream chunks into geoparquet file
        schema = pa.schema(pa_cols, metadata=encode_geoparquet_metadata(crs))

        with ParquetWriter(
            dest_file, schema, version="2.6", compression="SNAPPY"
        ) as writer:
            data: List[List[Any]] = [[] for _ in col_range]

            # Don't use the iterator but instead go by index and catch potential issues, primarily
            # when the metadata count is larger than the actual count of records
            # See: https://github.com/stactools-packages/fws-nwi/issues/2
            for i in range(count):
                row_num = i + 1
                error_write = False

                try:
                    shape = reader.shape(i)
                    geometry = to_geom(shape.__geo_interface__)
                    data[0].append(shapely.wkb.dumps(geometry))

                    record = reader.record(i)
                    for j in range(len(record)):
                        data[j + 1].append(record[j])
                except struct.error as err:
                    logger.warn(
                        (
                            "The count of records/shapes in the metadata is likely higher than the"
                            " actual number of records/shapes. Handling this gracefully, but the"
                            " resulting files might also be incomplete."
                            f" Row number (zero-based): {i}"
                            " Error: " + str(err)
                        )
                    )
                    # If there's data available, write it now to avoid that the last rows get lost
                    error_write = len(data) > 0

                if (row_num % 2500) == 0 or row_num == count or error_write:
                    table = pa.Table.from_arrays(data, schema=schema)
                    writer.write_table(table)
                    data = [[] for _ in col_range]

        # Create asset metadata
        asset_dict = create_asset_metadata(content_type, dest_file)
        # Can't use table extension: https://github.com/stac-utils/pystac/issues/872
        asset_dict["table:primary_geometry"] = constants.PARQUET_GEOMETRY_COL
        asset_dict["table:columns"] = stac_table_cols
        asset_dict["table:row_count"] = count
        asset = Asset.from_dict(asset_dict)

        # Projection info
        if base_crs != crs:
            proj_ext = ProjectionExtension.ext(asset)
            epsg = crs.to_epsg()
            if epsg is None:
                proj_ext.projjson = crs.to_json_dict()
            else:
                proj_ext.epsg = epsg

        logger.info(f"Converted {src_file} to {dest_file}")
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


def get_pyarrow_type(type: Optional[str]) -> Any:
    if type == "string":
        return pa.string()
    elif type == "int8":
        return pa.int8()
    elif type == "int16":
        return pa.int16()
    elif type == "int32":
        return pa.int32()
    elif type == "int64":
        return pa.int64()
    elif type == "float16":
        return pa.float16()
    elif type == "float32":
        return pa.float32()
    elif type == "float64":
        return pa.float64()
    elif type == "boolean":
        return pa.bool_()
    elif type == "datetime":
        return pa.timestamp()
    else:
        raise Exception(f"Unknown datatype, got {type}")


def encode_geoparquet_metadata(crs: CRS) -> Dict[bytes, bytes]:
    projjson = crs.to_json_dict()
    remove_id_from_member_of_ensembles(projjson)

    column_metadata = {}
    column_metadata[constants.PARQUET_GEOMETRY_COL] = {
        "encoding": "WKB",
        "crs": projjson,
        "geometry_type": constants.PARQUET_GEOMETRY_TYPE,  # todo: or ["Polygon", "MultiPolygon"]?
    }

    metadata = {
        "primary_column": constants.PARQUET_GEOMETRY_COL,
        "columns": column_metadata,
        "version": "0.4.0",
    }
    return {b"geo": json.dumps(metadata).encode("utf-8")}


# Source: https://github.com/geopandas/geopandas/blob/v0.11.1/geopandas/io/arrow.py#L51
def remove_id_from_member_of_ensembles(json_dict: Dict[str, Any]) -> None:
    """
    Older PROJ versions will not recognize IDs of datum ensemble members that
    were added in more recent PROJ database versions.
    Cf https://github.com/opengeospatial/geoparquet/discussions/110
    and https://github.com/OSGeo/PROJ/pull/3221
    Mimicking the patch to GDAL from https://github.com/OSGeo/gdal/pull/5872
    """
    for key, value in json_dict.items():
        if isinstance(value, dict):
            remove_id_from_member_of_ensembles(value)
        elif key == "members" and isinstance(value, list):
            for member in value:
                member.pop("id", None)
