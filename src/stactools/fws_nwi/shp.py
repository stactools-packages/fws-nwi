import logging
import os
from typing import Any, Dict, Optional

import shapefile
from pystac import Item, Link
from shapely.geometry import Polygon, shape
from shapely.ops import unary_union

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


def get_geometry(path: str, fallback: Optional[str] = None) -> Polygon:
    if os.path.exists(path):
        with shapefile.Reader(path) as shp:
            if len(shp) != 1:
                raise Exception("Geometry file should only contain a single shape")
            return shape(shp.shape(0).__geo_interface__)
    elif fallback is not None and os.path.exists(fallback):
        # Fallback: Geometry generated from other layer (e.g. wetlands project metadata)
        # 1. union
        # 2. buffer (100m)
        # 3. simplifing (douglas-peucker, 1000m)
        with shapefile.Reader(fallback) as shp:
            shapes = [shape(s.__geo_interface__) for s in shp.shapes()]
            return (
                unary_union(shapes).buffer(100).simplify(1000, preserve_topology=False)
            )
    else:
        raise Exception("Geometry can't be determined")


def get_lineage(path: str, content_type: Types) -> str:
    with shapefile.Reader(path) as shp:
        records = shp.records()
        if len(records) > 0:
            title = content_type.value.replace("_", " ")
            text = f"#### {title}\n"
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
            return text + "\n\n"
        else:
            return ""


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
