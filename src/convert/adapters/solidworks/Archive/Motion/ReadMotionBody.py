from functools import partial as PartialValue
from uuid import UUID

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Motion.MotionLayouts import (
    KMotionKey,
    KMotionLayouts,
    KMotionMgr,
    KMotionSchemas,
)
from convert.adapters.solidworks.Archive.Motion.MotionStudy import MotionStudy
from convert.adapters.solidworks.Archive.Motion.WriteMotionBody import WriteMotionBody
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    ReadRows,
    RequireRecord,
)


# a decoded owned study must retain its actual self link and match the complete bounded constructor body
def ReadMotionBody(CursorValue: BinaryReader) -> MotionStudy:
    StartValue = CursorValue.GetOffset()
    if CursorValue.ReadUnsigned(4) != 19000:
        raise ValueError("assembly motion requires archive version 19000")
    ContextValue = BodyContext(19000, KMotionLayouts, {}, KMotionSchemas)
    ReaderValue = GraphReader(
        CursorValue,
        ArchiveMaps(1),
        PartialValue(ReadBodyMut, ContextValue),
        RequireCanonicalTags=True,
    )
    RootValue = ArchiveNode.RequireNode(ReadNodeMut(ReaderValue))
    RowsValue = ReadRows(RootValue.FieldsValue.get("studies"))
    if RootValue.ClassValue != KMotionMgr or len(RowsValue) != 1:
        raise ValueError("assembly motion requires the actual singleton manager")
    StudyValue = ReadMotionKey(ArchiveNode.RequireNode(RowsValue[0].get("o")))
    SpanValue = CursorValue.BytesValue[StartValue : CursorValue.GetOffset()]
    if WriteMotionBody(StudyValue) != SpanValue:
        raise ValueError(
            "assembly motion body differs from the ordinary inactive study"
        )
    return StudyValue


# caption and uuid must come from the registered study while the embedded controller refers back to that object
def ReadMotionKey(NodeValue: ArchiveNode) -> MotionStudy:
    FieldsValue = NodeValue.FieldsValue
    LabelValue = FieldsValue.get("f0f8")
    IdentityValue = FieldsValue.get("f108")
    Controller = RequireRecord(FieldsValue.get("f2c8"))
    if (
        NodeValue.ClassValue != KMotionKey
        or Controller.get("f08") is not NodeValue
        or not isinstance(LabelValue, str)
        or not isinstance(IdentityValue, str)
    ):
        raise ValueError("assembly motion requires an actual self owned study")
    return MotionStudy(UUID(IdentityValue), LabelValue)
