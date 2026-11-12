from dataclasses import dataclass as MakeDataClass
from typing import Literal


@MakeDataClass(frozen=True, slots=True)
class DocumentSpec:
    Title: str
    ParamName: str
    LengthMm: float
    ProfileKind: Literal["parameter", "circle", "extrusion"] = "extrusion"
    RadiusMm: float = 12.5
    ParamComment: str = ""
    SketchName: str = "Authored Circle"
    ExtrusionName: str = "Authored Extrusion"
    BodyName: str = "Authored Cylinder"
