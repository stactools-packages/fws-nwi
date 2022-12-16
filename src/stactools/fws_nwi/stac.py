from pathlib import Path
from typing import Dict, Optional

import shapely.geometry
from pyproj.enums import WktVersion
from pystac import (
    Asset,
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

from stactools.fws_nwi import geoparquet
from stactools.fws_nwi.constants import (
    COLLECTION_BBOXES,
    DATETIME,
    DESCRIPTION,
    KEYWORDS,
    LINK_FACT_SHEET,
    LINK_LANDING_PAGE,
    LINK_LICENSE,
    LINK_METADATA,
    NWI_EXTENSION,
    PROVIDER_USFWS,
    TITLE,
    ZIPFILE_ASSET_KEY,
)
from stactools.fws_nwi.metadata import Metadata
from stactools.fws_nwi.states import States


def create_collection() -> Collection:
    collection = Collection(
        id="fws-nwi",
        description=DESCRIPTION,
        title=TITLE,
        keywords=KEYWORDS,
        license="proprietary",
        providers=[PROVIDER_USFWS],
        extent=Extent(
            spatial=SpatialExtent(COLLECTION_BBOXES),
            temporal=TemporalExtent([[DATETIME, DATETIME]]),
        ),
    )
    collection.add_links(
        [LINK_METADATA, LINK_FACT_SHEET, LINK_LANDING_PAGE, LINK_LICENSE]
    )
    collection.summaries = Summaries(
        {
            "fws_nwi:state": States.names(),
            "fws_nwi:state_code": States.codes(),
            "fws_nwi:content": ["riparian", "historic_wetlands", "wetlands"],
        },
        # Up the maxcount, otherwise the state arrays will be omitted from output
        maxcount=len(States) + 1,
    )

    item_assets = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets.item_assets = {
        "zip": AssetDefinition.create(
            title=None,
            description=None,
            media_type="application/zip",
            roles=["data", "archive", "source"],
        )
    }

    return collection


def create_item(
    zipfile_path: Path, geoparquet_directory: Optional[Path] = None
) -> Item:
    assets = {
        ZIPFILE_ASSET_KEY: create_zipfile_asset(zipfile_path),
    }
    if geoparquet_directory:
        assets.update(
            create_geoparquet_assets_from_zipfile(zipfile_path, geoparquet_directory)
        )
    return create_item_from_assets(assets)


def create_item_from_assets(assets: Dict[str, Asset]) -> Item:
    zipfile_asset = assets.get(ZIPFILE_ASSET_KEY, None)
    if zipfile_asset is None:
        raise Exception("a zipfile asset is required to create an item")
    metadata = Metadata.from_zipfile(
        Path(zipfile_asset.href)
    )  # TODO guard against URLs
    item = Item(
        id=metadata.state_code,
        geometry=shapely.geometry.mapping(metadata.geometry),
        bbox=metadata.geometry.bounds,
        datetime=DATETIME,
        properties={
            "fws_nwi:state": metadata.state,
            "fws_nwi:state_code": metadata.state_code,
            "fws_nwi:content": metadata.content,
        },
        stac_extensions=[NWI_EXTENSION],
    )
    for pdf in metadata.pdfs:
        item.add_link(
            Link(
                target=pdf.href,
                media_type=MediaType.PDF,
                title=pdf.title,
                rel="archives",
            )
        )
    item.assets = assets

    projection = ProjectionExtension.ext(item, add_if_missing=True)
    projection.epsg = metadata.crs.to_epsg()
    if projection.epsg is None:
        projection.wkt2 = metadata.crs.to_wkt(WktVersion.WKT2_2019)

    if any(
        any(k.startswith("table:") for k in a.extra_fields.keys())
        for a in item.assets.values()
    ):
        TableExtension.add_to(item)

    return item


def create_zipfile_asset(path: Path) -> Asset:
    return Asset(
        href=str(path),
        title=path.stem,
        description=f"{path.stem} source zipfile",
        media_type="application/zip",
        roles=["data", "archive", "source"],
    )


def create_geoparquet_assets_from_zipfile(
    path: Path, directory: Path
) -> Dict[str, Asset]:
    metadatas = geoparquet.from_zipfile(path, directory)
    assets = {}
    for metadata in metadatas:
        roles = ["data", "cloud-optimized"]
        if metadata.role:
            roles.append(metadata.role)
        asset = Asset(
            href=str(metadata.path),
            title=metadata.title,
            description=metadata.description,
            media_type="application/x-parquet",
            roles=roles,
            extra_fields={
                "table:primary_geometry": metadata.primary_geometry,
                "table:columns": metadata.columns,
                "table:row_count": metadata.row_count,
            },
        )
        assets[metadata.key] = asset
    return assets
