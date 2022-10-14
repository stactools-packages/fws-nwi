import logging
from typing import Any, Dict, Optional

from . import constants

logger = logging.getLogger(__name__)


def create_asset_metadata(href: Optional[str] = None) -> Dict[str, Any]:
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
    }
    if href is not None:
        asset["href"] = href
    return asset
