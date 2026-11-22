from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Assembly.NestedIndex.AsmMatrix import AsmMatrix
from convert.adapters.solidworks.Core.TypedMates.ReadMateFrame import ReadMateFrame
from interchange.assembly.ComponentInstance import ComponentInst


# a reopened placement keeps its validated physical basis and translation without orthogonalizing twice
def ReadExactPlace(Value: ComponentInst) -> OccurrenceIn:
    StoredValue = Value.attributes.get("typed_placement_m")
    if type(StoredValue) is not tuple:
        raise ValueError(
            "reopened nested occurrence requires its checked physical pose"
        )
    PoseValue = ReadMateFrame(CastValue(tuple[float, ...], StoredValue))
    if AsmMatrix(PoseValue) != Value.transform:
        raise ValueError("reopened nested occurrence differs from its physical pose")
    return OccurrenceIn(
        Value.name,
        PlaneFrame(
            (PoseValue[12], PoseValue[13], PoseValue[14]),
            (PoseValue[0], PoseValue[1], PoseValue[2]),
            (PoseValue[4], PoseValue[5], PoseValue[6]),
            (PoseValue[8], PoseValue[9], PoseValue[10]),
        ),
    )
