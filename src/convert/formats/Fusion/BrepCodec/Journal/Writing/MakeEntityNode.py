from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeTopology import MakeTopology
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeCarriers import MakeCarriers
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeAttributes import (
    MakeAttributes,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)

from convert.formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode


def MakeEntityNode(Value: KJournalEntity) -> AsmRecord:
    if isinstance(Value, (PointNode, PlaneNode, EllipseNode, ConeNode, StraightNode)):
        return MakeCarriers(Value)
    if isinstance(Value, (TimeAttrib, TrackAttrib, TagAttrib, SketchAttrib)):
        return MakeAttributes(Value)
    return MakeTopology(Value)
