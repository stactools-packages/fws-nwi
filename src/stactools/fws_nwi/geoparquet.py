from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from zipfile import ZipFile

import geopandas
import stac_table

from stactools.fws_nwi import metadata as zipfile_metadata


@dataclass
class Metadata:
    key: str
    path: Path
    title: str
    description: str
    role: Optional[str]
    columns: List[Dict[str, Any]]
    primary_geometry: str
    row_count: int


def from_zipfile(path: Path, directory: Path) -> List[Metadata]:
    metadatas = []
    with ZipFile(path) as zipfile:
        for name in (n for n in zipfile.namelist() if n.endswith(".shp")):
            geoparquet_path = directory / (Path(name).stem + ".geoparquet")
            dataframe = geopandas.read_file(f"zip://{path}!{name}")
            row_count = len(dataframe)
            primary_geometry = dataframe.geometry.name
            dataframe.to_parquet(geoparquet_path)
            dataset = stac_table.parquet_dataset_from_url(str(geoparquet_path), None)
            columns = stac_table.get_columns(dataset)
            key = geoparquet_path.stem
            title = key.replace("_", " ")
            role = zipfile_metadata.role(name)
            metadatas.append(
                Metadata(
                    key=key,
                    path=geoparquet_path,
                    title=title,
                    description=f"{title} geoparquet",
                    role=role,
                    row_count=row_count,
                    primary_geometry=primary_geometry,
                    columns=columns,
                )
            )
    return metadatas
