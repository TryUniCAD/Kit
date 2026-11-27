from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Native.Circular.DualFrames.LocalDualVector import (
    LocalDualVector,
)
from convert.adapters.Fusion.Native.DatumPrism.ReadDatumFrame import LocalDatum
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from interchange.geometry.Models.Transform import Transform


# rigid comparison changes coordinates while retaining every topology reference and attribute field
def LocalDualEntity(Entity: KJournalEntity, Frame: Transform) -> KJournalEntity:
    if isinstance(Entity, ConeNode):
        return ReplaceData(
            Entity,
            OriginCm=LocalDatum(Frame, Entity.OriginCm),
            AxisVector=LocalDualVector(Entity.AxisVector, Frame),
            MajorAxisCm=LocalDualVector(Entity.MajorAxisCm, Frame),
        )
    if isinstance(Entity, EllipseNode):
        return ReplaceData(
            Entity,
            OriginCm=LocalDatum(Frame, Entity.OriginCm),
            Normal=LocalDualVector(Entity.Normal, Frame),
            MajorAxisCm=LocalDualVector(Entity.MajorAxisCm, Frame),
        )
    if isinstance(Entity, PlaneNode):
        return ReplaceData(
            Entity,
            OriginCm=LocalDatum(Frame, Entity.OriginCm),
            Normal=LocalDualVector(Entity.Normal, Frame),
            ReferenceAxis=LocalDualVector(Entity.ReferenceAxis, Frame),
        )
    if isinstance(Entity, PointNode):
        return ReplaceData(Entity, PositionCm=LocalDatum(Frame, Entity.PositionCm))
    return Entity
