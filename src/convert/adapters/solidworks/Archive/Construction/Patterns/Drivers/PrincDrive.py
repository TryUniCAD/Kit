from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)


# principal pitch retains distinct sketch normal dimension frame and annotation view ownership
@DataClass(frozen=True, slots=True)
class PrincDrive:
    FrameValue: PlaneFrame
    SketchNormal: KDatumVector
    PitchView: str
