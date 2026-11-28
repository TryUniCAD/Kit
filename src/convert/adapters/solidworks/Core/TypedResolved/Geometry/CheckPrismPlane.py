from collections.abc import Mapping
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismDatum import (
    CheckPrismDatum,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismAtom import (
    CheckPrismAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismProf import (
    CheckPrismProf,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import (
    ReadDatumFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckOriginGeom import (
    CheckOriginGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# all principal datums and the model origin must remain ordinary geometry even when only one plane supports the solid
def CheckPrismPlane(
    Features: Mapping[int, ArchiveNode], RootValue: ArchiveNode
) -> None:
    PlanesValue = tuple(
        NodeValue
        for NodeValue in Features.values()
        if NodeValue.ClassValue.NameValue == "moRefPlane_c"
    )
    if {ReadDatumFrame(NodeValue)[1] for NodeValue in PlanesValue} != {1, 2, 3}:
        raise ValueError(
            "cache free prism requires three actual principal datum frames"
        )
    (OriginValue,) = (
        NodeValue
        for NodeValue in Features.values()
        if NodeValue.ClassValue.NameValue == "moOriginProfileFeature_c"
    )
    for NodeValue in PlanesValue:
        CheckPrismAtom(NodeValue)
        CheckPrismDatum(NodeValue)
        Fields = NodeValue.FieldsValue
        if (
            Fields.get("f6e8") is not None
            or Fields.get("f6e0") != 0
            or Fields.get("f6f0") != 0
            or Fields.get("f6dc") not in (1, 5)
            or any(
                NativeRecord(Fields.get("f6c0")).get(FieldName) != 0.0
                for FieldName in ("x", "y", "z")
            )
        ):
            raise ValueError("cache free prism has unsupported principal plane state")
        if not IsLineState(Fields.get("f368")) or not IsLineState(Fields.get("f388")):
            raise ValueError("cache free prism principal plane has extra references")
    CheckPrismProf(OriginValue)
    _ = ReadPrismFrame(OriginValue, RootValue, Features)
    CheckOriginGeom(OriginValue)
