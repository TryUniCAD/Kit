from collections.abc import Mapping

from convert.adapters.freecad.BodyLineage.BoxNativeOwner import ReadBoxArchive
from convert.adapters.freecad.Native import NativeObjectA
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.BoxDatums import (
    BoxDatums,
    BoxOriginPoint,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadAxisPlace import (
    ReadAxisFrame,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxRelease import (
    ReadBoxRelease,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadOriginAxes import (
    IsAxisShown,
    ReadAxLabel,
    ReadDatumProps,
    ReadOriginAxes,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    ReadBoxString,
    RequireBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    RequireProp,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Transform import KTransformIdentity


# a built in fixed point uses its own checked placement without borrowing a sketch coordinate
def ReadBoxPoint(Record: Mapping[str, object], OriginId: str) -> BoxOriginPoint:
    Properties = ReadDatumProps(Record, "Origin", "App::Point", "1.1")
    Frame = ReadAxisFrame(Properties)
    RequireBox(
        Frame == KTransformIdentity and IsAxisShown(Properties),
        "FreeCAD origin point requires its fixed visible principal placement",
    )
    return BoxOriginPoint(
        OriginId,
        ReadBoxString(Record["object_id"]),
        ReadBoxString(Record["name"]),
        ReadAxLabel(Properties),
        Frame.origin,
        True,
    )


# the body origin and its datums must all agree with the authenticated in memory object table
def ReadBoxDatums(DocumentValue: CadDocument) -> BoxDatums:
    Metadata = NativeRecord(DocumentValue.metadata["freecad"])
    Archive = ReadBoxArchive(DocumentValue)
    RowsValue = NativeRows(Metadata["objects"])
    if RowsValue != tuple(NativeObjectA(Value) for Value in Archive.objects):
        raise ValueError("FreeCAD origin datum owners disagree with the source archive")
    if len(DocumentValue.bodies) != 1:
        raise ValueError("FreeCAD origin datums require their actual solid body")
    BodyData = NativeRecord(DocumentValue.bodies[0].attributes["freecad"])
    if BodyData not in RowsValue or BodyData["type_id"] != "PartDesign::Body":
        raise ValueError("FreeCAD body cannot identify its actual origin owner")
    RequireProp(
        NativeRecord(BodyData["properties"]), "Origin", "Link", "Link", "Origin"
    )
    AxisValue = ReadOriginAxes(DocumentValue, CheckPlanes=True)
    if ReadBoxRelease(DocumentValue.source.application_version) != "1.1":
        return BoxDatums(AxisValue, None)
    (PointRecord,) = (
        RowValue for RowValue in RowsValue if RowValue["name"] == "Origin001"
    )
    return BoxDatums(AxisValue, ReadBoxPoint(PointRecord, AxisValue.OriginId))
