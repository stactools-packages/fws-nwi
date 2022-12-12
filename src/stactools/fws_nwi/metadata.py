from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Tuple
from zipfile import ZipFile

import fiona
import fiona.crs
import shapely.geometry
import shapely.ops
import stactools.core.projection
from pyproj import CRS

from stactools.fws_nwi.states import States

SIMPLIFY = 1000  # 1km


@dataclass
class Pdf:
    href: str
    title: Optional[str]


@dataclass
class Metadata:
    geometry: Any
    crs: CRS
    state: str
    state_code: str
    content: List[str]
    pdfs: List[Pdf]

    @classmethod
    def from_zipfile(cls, path: Path) -> "Metadata":
        state_code = path.stem.split("_")[0]
        state = States[state_code]
        content = set()
        pdfs = []
        geometry = None
        crs = None
        with ZipFile(path) as zipfile:
            for name in (n for n in zipfile.namelist() if n.endswith(".shp")):
                maybe_content = role(name)
                if maybe_content:
                    content.add(maybe_content)
                with fiona.open(f"zip://{path}!{name}") as shapefile:
                    if len(shapefile) == 1:
                        for record in shapefile:
                            geometry = shapely.geometry.shape(
                                record["geometry"]
                            ).simplify(SIMPLIFY)
                            crs = fiona.crs.to_string(shapefile.crs)
                            geometry = stactools.core.projection.reproject_geom(
                                crs,
                                "EPSG:4326",
                                shapely.geometry.mapping(geometry),
                                precision=6,
                            )
                    if "PDF_HYPERL" in shapefile.schema["properties"]:
                        for record in shapefile:
                            href = record["properties"].get("PDF_HYPERL", None)
                            if href:
                                title = record["properties"].get("PDF_NAME")
                                if title and title.endswith(".pdf"):
                                    title = title[0:-4]
                                pdfs.append(Pdf(href=href, title=title))
        if geometry is None:
            geometry, crs = calculate_geometry(path)
        else:
            geometry = shapely.geometry.shape(geometry)
        return cls(
            geometry=geometry,
            crs=CRS(crs),
            state_code=state_code,
            state=state,
            content=list(content),
            pdfs=pdfs,
        )


def role(name: str) -> Optional[str]:
    name = name.split("/")[-1].split(".")[0]
    parts = name.split("_")
    if len(parts) <= 1:
        return None
    elif len(parts) >= 3 and parts[1] == "Historic" and parts[2] == "Wetlands":
        return "historic_wetlands"
    elif parts[1] == "Wetlands":
        if name.endswith("Historic_Map_Info") or name.endswith("Project_Metadata"):
            return None
        else:
            return "wetlands"
    elif parts[1] == "Riparian":
        return "riparian"
    else:
        return None


def calculate_geometry(path: Path) -> Tuple[Any, str]:
    crses = set()
    zipfile_geometries = list()
    with ZipFile(path) as zipfile:
        for name in (n for n in zipfile.namelist() if n.endswith(".shp")):
            with fiona.open(f"zip://{path}!{name}") as shapefile:
                crses.add(fiona.crs.to_string(shapefile.crs))
                geometries = []
                for record in shapefile:
                    geometry = record["geometry"]
                    if geometry["type"] in ("Polygon", "MultiPolygon"):
                        geometries.append(shapely.geometry.shape(geometry))
                geometry = shapely.ops.unary_union(geometries)
                geometry = shapely.geometry.shape(geometry)
                if geometry.is_valid:
                    zipfile_geometries.append(geometry)
    if len(crses) == 1:
        geometry = shapely.ops.unary_union(zipfile_geometries).simplify(SIMPLIFY)
        crs = crses.pop()
        geometry = stactools.core.projection.reproject_geom(
            crs, "EPSG:4326", shapely.geometry.mapping(geometry), precision=6
        )
        return shapely.geometry.shape(geometry), crs
    else:
        raise Exception(f"multiple crses in shapefile: {crses}")
