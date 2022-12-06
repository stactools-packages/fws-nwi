from pathlib import Path

from stactools.fws_nwi import geoparquet


def test_to_geoparquet(dc_zipfile: Path, tmp_path: Path) -> None:
    paths = geoparquet.from_zip(dc_zipfile, tmp_path)
    assert len(paths) == 4
