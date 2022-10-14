import logging
from typing import Any, Dict, List, Optional

from . import constants

logger = logging.getLogger(__name__)


def create_asset_metadata(
    title: str,
    href: Optional[str] = None,
    cols: List[Dict[str, Any]] = [],
    count: int = -1,
) -> Dict[str, Any]:
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
    if len(cols) > 0:
        asset["table:columns"] = cols
    if count >= 0:
        asset["table:row_count"] = int(count)
    return asset
