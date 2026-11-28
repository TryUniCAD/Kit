from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.CurveRecords import (
    ParIntCur,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.SweepPaths import LawPath
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.SweepPaths import PathHead
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.SweepRecords import (
    SweepProfile,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.SweepRecords import SweepSur
from convert.Formats.Fusion.BrepCodec.Frustum.Models.ConeFrame import ConeFrame
from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.Formats.Fusion.BrepCodec.Frustum.Models.RimFrame import RimFrame
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NestedTag import NestedTag
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.MaterialAttrib import (
    MaterialAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    LoftSubdata,
    SubtypeNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.CurveRecords import (
    CurveContext,
    ExactIntCur,
    ExpParCur,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.LoftRecords import (
    LoftPiece,
    LoftSection,
    LoftSplSur,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.SurfaceRecords import (
    SplineCommon,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.Formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.Formats.Fusion.BrepCodec.Journal.States.BulletinBoard import BulletinBoard
from convert.Formats.Fusion.BrepCodec.Journal.States.BulletinChange import (
    BulletinChange,
)
from convert.Formats.Fusion.BrepCodec.Journal.States.DeltaState import DeltaState
from convert.Formats.Fusion.BrepCodec.Journal.States.StreamState import StreamState
from convert.Formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.Formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.Formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.BrepCodec.Models.VertexIndices import VertexIndices
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismEdge import PrismEdge
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismIds import PrismIds
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismLine import PrismLine
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismPlane import PrismPlane
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags

# the boundary representation types order must stay explicit so public document claims remain grounded in native records
KBrepTypes: tuple[type[object], ...] = (
    ParIntCur,
    LawPath,
    PathHead,
    SweepProfile,
    SweepSur,
    CurveContext,
    ExactIntCur,
    IntcurveNode,
    ChoiceValue,
    LoftSubdata,
    SubtypeNode,
    BsCurve,
    BsSurface,
    ExpParCur,
    LoftPiece,
    LoftSection,
    LoftSplSur,
    SplineCommon,
    PcurveNode,
    SplineNode,
    SubtypeRef,
    TorusNode,
    ConeFrame,
    FrustumFrame,
    FrustumHistory,
    RimFrame,
    AttribLinks,
    NestedTag,
    SketchAttrib,
    TagAttrib,
    MaterialAttrib,
    TimeAttrib,
    TrackAttrib,
    AsmRoot,
    BodyNode,
    CoedgeNode,
    ConeNode,
    EdgeNode,
    EllipseNode,
    EntityPrefix,
    FaceNode,
    LoopNode,
    LumpNode,
    PlaneNode,
    PointNode,
    ShellNode,
    StraightNode,
    TransformNode,
    VertexNode,
    JournalModel,
    GeometryState,
    BulletinBoard,
    BulletinChange,
    DeltaState,
    StreamState,
    BodyIdentity,
    BrepHeader,
    EntityIds,
    FeatureTag,
    HistoryModel,
    HistoryState,
    SketchLink,
    SnapshotModel,
    TopologyTags,
    VertexIndices,
    PrismEdge,
    PrismFrame,
    PrismIds,
    PrismHistory,
    PrismLine,
    PrismPlane,
    PrismTags,
)
