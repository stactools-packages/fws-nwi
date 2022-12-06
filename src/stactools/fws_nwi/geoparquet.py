from pathlib import Path
from typing import List
from zipfile import ZipFile

import geopandas


def from_zip(path: Path, directory: Path) -> List[Path]:
    paths = []
    with ZipFile(path) as zipfile:
        for name in (n for n in zipfile.namelist() if n.endswith(".shp")):
            geoparquet_path = directory / (Path(name).stem + ".geoparquet")
            dataframe = geopandas.read_file(f"zip://{path}!{name}")
            dataframe.to_parquet(geoparquet_path)
            paths.append(geoparquet_path)
    return paths
