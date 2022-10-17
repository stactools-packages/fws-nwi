import logging
from typing import Any, Dict

from . import constants
from .content import Types, wetlands_area_name

logger = logging.getLogger(__name__)


def create_asset_metadata(content_type: Types, href: str) -> Dict[str, Any]:
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
    if content_type == Types.WETLANDS:
        title = wetlands_area_name(href)
    else:
        title = content_type.value

    asset: Dict[str, Any] = {
        "title": f"{title} GeoParquet file",
        "type": constants.PARQUET_MEDIA_TYPE,
        "roles": constants.PARQUET_ROLES + [content_type.value.lower()],
        "href": href,
        "table:primary_geometry": constants.PARQUET_GEOMETRY_COL,
    }

    return asset
