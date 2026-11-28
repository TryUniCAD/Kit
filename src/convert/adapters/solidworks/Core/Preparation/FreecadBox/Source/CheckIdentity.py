from collections.abc import Mapping

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    ReadBoxString,
    RequireBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    ReadPropChild,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# offsets and body frames cannot introduce an unqualified placement
def CheckIdentity(Properties: Mapping[str, object], NameValue: str) -> None:
    Placement = ReadPropChild(Properties[NameValue], "Placement", "PropertyPlacement")
    Attributes = NativeRecord(Placement["attributes"])
    Translation = tuple(
        float(ReadBoxString(Attributes[AxisName])) for AxisName in ("Px", "Py", "Pz")
    )
    Quaternion = tuple(
        float(ReadBoxString(Attributes[AxisName]))
        for AxisName in ("Q0", "Q1", "Q2", "Q3")
    )
    RequireBox(
        Translation == (0.0, 0.0, 0.0)
        and Quaternion[:3] == (0.0, 0.0, 0.0)
        and abs(Quaternion[3]) == 1.0
        and float(ReadBoxString(Attributes["A"])) == 0.0,
        f"FreeCAD {NameValue} requires explicit support placement",
    )
