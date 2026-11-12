from typing import TypeAlias

from convert.formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
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

KJournalEntity: TypeAlias = (
    AsmRoot
    | BodyNode
    | LumpNode
    | ShellNode
    | FaceNode
    | LoopNode
    | CoedgeNode
    | EdgeNode
    | VertexNode
    | PointNode
    | PlaneNode
    | EllipseNode
    | StraightNode
    | ConeNode
    | TimeAttrib
    | TrackAttrib
    | TagAttrib
    | SketchAttrib
)
