import logging
from typing import Any, Dict, List, Optional

from . import constants

# import shapefile


logger = logging.getLogger(__name__)


def create_asset_metadata(
    href: Optional[str] = None,
    geom_col: Optional[str] = None,
    cols: List[Dict[str, Any]] = [],
    count: int = -1,
) -> Dict[str, Any]:
    """
    Creates an asset dict with the basic and table properties for the ZIP file
    containing the shapefile. An href should be given for normal assets, but
    can be None for Item Asset Definitions.

    Args:
        href (str): The URL to the asset (optional)
        geom_col (str): Name of the column for the primary geometry (optional)
        cols (List[Dict[str, Any]]): A list of columns (optional;
            compliant to table:columns)
        count: The number of rows in the asset (optional)

    Returns:
        dict: Basic Asset object
    """
    asset: Dict[str, Any] = {
        "title": constants.SHP_TITLE,
        "type": constants.SHP_MEDIA_TYPE,
        "roles": constants.SHP_ROLES,
        "description": constants.SHP_DESCRIPTION,
    }
    if href is not None:
        asset["href"] = href
    if geom_col is not None:
        asset["table:primary_geometry"] = geom_col
    if len(cols) > 0:
        asset["table:columns"] = cols
    if count >= 0:
        asset["table:row_count"] = int(count)
    return asset
