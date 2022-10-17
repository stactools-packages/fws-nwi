import enum
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

INCONSISTENT_DATA_FILES = [
    "Colorado_Wetlands_East",
    "South_Dakota_East",
    "Wisconsin_Wetlands_South",
]


CAMEL_CASE_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")


class Types(str, enum.Enum):
    HIST_WETLANDS = "Historic_Wetlands"
    RIPARIAN = "Riparian"
    WETLANDS = "Wetlands"

    @classmethod
    def values(self) -> List[str]:
        return [i.value for i in Types]


@dataclass
class TypeFiles:
    """Class to represent the available files for the content types."""

    type: Types
    files: List[str]  # primary data files
    projects: Optional[str] = None  # project metadata
    archive: Optional[str] = None  # historic map info


def parse(shapefiles: List[str], code: str, folder: str) -> Dict[Types, TypeFiles]:
    content = {}
    for type in Types:
        files = []
        projects = None
        archive = None

        for file in shapefiles:
            # Detect primary data files
            name = file[0:-4]  # remove .shp
            if name == f"{code}_{type}" or name in INCONSISTENT_DATA_FILES:
                files.append(file)
            elif type == Types.WETLANDS and re.match(
                r"([A-Z]{2,4}|PacTrust)_Wetlands_(East|West|North|South|Central)", name
            ):
                files.append(file)

            # Detect project metadata file
            if type == Types.WETLANDS and re.match(
                r"([A-Z]{2,4}|PacTrust)_(Wetlands_)?Project_Metadata", name
            ):
                projects = file
            elif type == Types.HIST_WETLANDS and re.match(
                r"([A-Z]{2,4}|PacTrust)_Historic_Wetlands_Project_Metadata", name
            ):
                projects = file
            elif type == Types.RIPARIAN and re.match(
                r"([A-Z]{2,4}|PacTrust)_Riparian_(Project_)?Metadata", name
            ):
                projects = file

            # Detect historic map info file (only for wetlands)
            if type == Types.WETLANDS and re.match(
                r"([A-Z]{2,4}|PacTrust)_(Wetlands_)?Historic_Map_Info", name
            ):
                archive = file

        content[type] = TypeFiles(
            type=type,
            files=[os.path.join(folder, file) for file in files],
            projects=os.path.join(folder, projects) if projects is not None else None,
            archive=os.path.join(folder, archive) if archive is not None else None,
        )

    return content


def parse_name(path: str, content_type: Types) -> str:
    name = os.path.basename(path)[0:-4]  # basename and remove .shp extension

    if content_type != Types.WETLANDS:
        return content_type.value

    # WETLANDS ONLY:
    # This is the only outlier right now, handle it specifically
    if name == "South_Dakota_East":
        return "Wetlands East"

    # Detect from usual file names by finding the text after e.g. Wetlands_ and then
    # converting the different casing methods (camel/snake case)
    index = name.find(f"{content_type.value}_")
    if index > -1:
        # Extract variable part from string (can be camel case or snake case)
        # snake case in this case has the first letter of a word being uppercased
        area = name[index:]
        # convert from snake case to camel case
        area = area.replace("_", "")
        # convert from camel case to "normal text"
        area = CAMEL_CASE_PATTERN.sub(" ", area)
        return area
    else:
        return "Wetlands"
