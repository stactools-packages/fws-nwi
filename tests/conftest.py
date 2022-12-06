from pathlib import Path

import pytest

from . import test_data


@pytest.fixture
def dc_zipfile() -> Path:
    return Path(test_data.get_path("data-files/DC_shapefile_wetlands.zip"))
