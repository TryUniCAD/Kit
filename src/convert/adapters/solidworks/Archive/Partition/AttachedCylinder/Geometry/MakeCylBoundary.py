from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.CylKeys import (
    KCylMantle,
    KCylSide,
    KCylWorld,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.CylSpan import (
    CylSpan,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.MakeAttCylFaces import (
    MakeAttCylFaces,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.MakeAttCylSide import (
    MakeAttCylSide,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.MakeAttRim import (
    MakeAttRim,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.MakeCylRimRef import (
    MakeCylRimRef,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeBoundRoot import (
    MakeBoundRoot,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakePrismNodes import (
    BindPrismFields,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# attachment adds the active world owner while retaining independent resident and entity allocation
def MakeCylBoundary(
    SpanValue: CylSpan,
) -> tuple[XmtNode, tuple[XmtNode, ...], tuple[XmtNode, XmtNode, XmtNode]]:
    NearValue, FarValue = MakeCylRimRef("near"), MakeCylRimRef("far")
    BodyValue, *Regions = MakeBoundRoot(
        KCylSide, NearValue.EdgeValue, NearValue.CurveValue, KCylMantle
    )
    CellsValue = (
        ReplaceValue(
            BodyValue, FieldsValue=dict(BodyValue.FieldsValue) | {"owner": KCylWorld}
        ),
        *Regions,
        *MakeAttCylFaces(NearValue, FarValue),
        *MakeAttCylSide(NearValue, FarValue, SpanValue),
        *MakeAttRim(NearValue, FarValue, SpanValue, True),
        *MakeAttRim(FarValue, NearValue, SpanValue, False),
    )
    Indices = {KCylWorld: 1} | {
        CellValue.RefValue: Position for Position, CellValue in enumerate(CellsValue, 2)
    }
    EntityId = 0
    LastEntity = sum(
        CellValue.RefValue.KindValue not in (12, 17) for CellValue in CellsValue
    )
    NodesValue: dict[object, XmtNode] = {}
    for CellValue in CellsValue:
        EntityId += int(CellValue.RefValue.KindValue not in (12, 17))
        NodesValue[CellValue.RefValue] = BindPrismFields(
            CellValue, Indices, EntityId, LastEntity
        )
    return (
        NodesValue[BodyValue.RefValue],
        tuple(NodesValue.values()),
        (
            NodesValue[NearValue.FaceValue],
            NodesValue[FarValue.FaceValue],
            NodesValue[KCylSide],
        ),
    )
