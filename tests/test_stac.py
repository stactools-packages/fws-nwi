from pathlib import Path

from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.table import TableExtension

from stactools.fws_nwi import stac


def test_create_collection() -> None:
    collection = stac.create_collection()
    collection.set_self_href("dummy value")
    collection.validate()


def test_create_item(dc_zipfile: Path) -> None:
    item = stac.create_item(dc_zipfile)
    assert item.id == "DC"
    assert item.properties["fws_nwi:state"] == "District of Columbia"
    assert item.properties["fws_nwi:state_code"] == "DC"
    assert item.properties["fws_nwi:content"] == ["wetlands"]

    archive_links = item.get_links("archives")
    assert len(archive_links) == 5

    assert (
        "https://stac-extensions.github.io/usfws-nwi/v1.0.0/schema.json"
        in item.stac_extensions
    )

    projection = ProjectionExtension.ext(item)
    assert projection.epsg
    assert projection.bbox

    assert "zip" in item.assets

    item.validate()


def test_create_item_with_geoparquet(dc_zipfile: Path, tmp_path: Path) -> None:
    item = stac.create_item(dc_zipfile, tmp_path)
    _ = TableExtension.ext(item)

    assert len(item.assets) == 5
    geoparquet_assets = [
        a for a in item.assets.values() if a.media_type == "application/x-parquet"
    ]
    assert len(geoparquet_assets) == 4
    for asset in geoparquet_assets:
        _ = TableExtension.ext(asset)
