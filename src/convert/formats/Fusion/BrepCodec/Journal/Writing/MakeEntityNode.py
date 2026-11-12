from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
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


from convert.formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)


def MakeEntityNode(Value: KJournalEntity) -> AsmRecord:
    if isinstance(
        Value,
        (
            PointNode,
            PlaneNode,
            EllipseNode,
            ConeNode,
            StraightNode,
            TransformNode,
            SphereNode,
            TorusNode,
            SplineNode,
            IntcurveNode,
            PcurveNode,
        ),
    ):
        return MakeCarriers(Value)
    if isinstance(Value, (TimeAttrib, TrackAttrib, TagAttrib, SketchAttrib)):
        return MakeAttributes(Value)
    return MakeTopology(Value)
