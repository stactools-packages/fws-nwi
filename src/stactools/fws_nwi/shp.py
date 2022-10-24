import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import shapefile
from pyproj import CRS, Transformer
from pystac import Item, Link
from shapely.geometry import Polygon
from shapely.geometry import shape as to_geom
from shapely.ops import transform, unary_union

from . import constants
from .content import Types

logger = logging.getLogger(__name__)


def create_asset_metadata(href: str) -> Dict[str, Any]:
    """
    Creates an asset dict with the basic and table properties for the ZIP file
    containing the shapefile. An href should be given for normal assets, but
    can be None for Item Asset Definitions.

    Args:
        href (str): The URL to the asset (optional)

    Returns:
        dict: Basic Asset object
    """
    asset: Dict[str, Any] = {
        "title": constants.SHP_TITLE,
        "type": constants.SHP_MEDIA_TYPE,
        "roles": constants.SHP_ROLES,
        "description": constants.SHP_DESCRIPTION,
        "href": href,
    }
    return asset


def get_type(field: List[Any]) -> Optional[str]:
    type = field[1]
    if type == "C":
        return "string"
    elif type == "N" or type == "F":
        if field[3] == 0:  # decimal length = 0 => int
            if field[2] <= 2:
                return "int8"
            elif field[2] <= 4:
                return "int16"
            elif field[2] <= 9:
                return "int32"
            else:
                return "int64"
        else:  # floats
            return "float64"  # ignore float16/32 for now
    elif type == "L":
        return "boolean"
    elif type == "D":
        return "datetime"
    else:
        return None


def get_projection(shp_path: str) -> CRS:
    folder = os.path.dirname(shp_path)
    filename = os.path.splitext(os.path.basename(shp_path))[0]
    proj_file = os.path.join(folder, f"{filename}.prj")
    if os.path.exists(proj_file):
        with open(proj_file, "r") as file:
            return CRS.from_string(file.read())
    else:
        logger.warn(
            f"No projection file found at {proj_file}, falling back to EPSG:5070"
        )
        return CRS.from_epsg(5070)


def get_geometry(
    path: str, fallback: Optional[str] = None
) -> Tuple[Polygon, Polygon, CRS]:
    # Returns as tuple:
    #   1. Polygon in native CRS
    #   2. Polygon in WGS84
    #   3. Native CRS
    if os.path.exists(path):
        logger.info(f"Reading geometry from {path}")
        crs = get_projection(path)
        with shapefile.Reader(path) as shp:
            if len(shp) != 1:
                raise Exception("Geometry file should only contain a single shape")
            geometry = to_geom(shp.shape(0).__geo_interface__)
    elif fallback is not None and os.path.exists(fallback):
        # Fallback: Geometry generated from other layer (e.g. wetlands project metadata)
        # 1. union
        # 2. buffer (10m)
        # 3. simplifing (douglas-peucker, 250m)
        logger.info(f"Computing geometry from {fallback}")
        crs = get_projection(fallback)
        with shapefile.Reader(fallback) as shp:
            shapes = [to_geom(s.__geo_interface__) for s in shp.shapes()]
            geometry = unary_union(shapes)
    else:
        raise Exception("Geometry can't be determined")

    # 10m buffer to close small gaps in some geometries
    geometry = geometry.buffer(10).simplify(250, preserve_topology=True)

    wgs84_geometry = toWgs84(crs, geometry)
    return (geometry, wgs84_geometry, crs)


def toWgs84(source_crs: CRS, geom: Polygon) -> Polygon:
    target_crs = CRS(4326)
    project = Transformer.from_crs(source_crs, target_crs, always_xy=True).transform
    return transform(project, geom)


def get_lineage(path: str, content_type: Types) -> str:
    logger.info(f"Loading lineage information from {path}")
    with shapefile.Reader(path) as shp:
        records = shp.records()
        if len(records) > 0:
            title = content_type.value.replace("_", " ")
            filename = os.path.basename(path)
            text = (
                f"#### {title}\n"
                f"For all details see the file `{filename}` in the source asset.\n\n"
            )
            for r in records:
                record = r.as_dict()
                name = record["PROJECT_NA"]
                link = record["SUPPMAPINF"]
                if link is not None and len(link) > 0 and link != "None":
                    name = f"[{name}]({link})"

                details = []
                if (
                    "STATUS" in record
                    and record["STATUS"] is not None
                    and record["STATUS"] != "No_Data"
                ):
                    details.append(record["STATUS"])

                if "IMAGE_YR" in record and record["IMAGE_YR"] != 0:
                    details.append(str(record["IMAGE_YR"]))

                if (
                    "DATA_CAT" in record
                    and record["DATA_CAT"] is not None
                    and record["DATA_CAT"] != "None"
                ):
                    details.append(record["DATA_CAT"])

                if len(name) == 0 and len(details) == 0:
                    continue

                if len(name) == 0:
                    name = "Unnamed project"

                details_formatted = ", ".join(details)
                heading = f"{name} ({details_formatted})"

                src = record["DATA_SOURC"]
                if src is not None and len(src) > 0 and src != "None":
                    heading = heading + f" with data from *{src}*"

                text = text + f"\n* {heading}"
            return text + "\n\n"
        else:
            return ""


def add_archive_links(item: Item, path: str) -> None:
    logger.info(f"Loading archive links from {path}")
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
