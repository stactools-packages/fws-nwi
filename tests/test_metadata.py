from pathlib import Path

from stactools.fws_nwi.metadata import Metadata


def test_from_zipfile(dc_zipfile: Path) -> None:
    _ = Metadata.from_zipfile(dc_zipfile)
