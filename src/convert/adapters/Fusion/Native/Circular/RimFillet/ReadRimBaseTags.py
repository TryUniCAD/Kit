from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.CheckRoundTags import CheckRoundTags
from convert.adapters.Fusion.Native.Circular.RimFillet.ReadRimTag import ReadRimTag
from convert.adapters.Fusion.Native.Circular.RimFillet.ReadRimOps import ReadRimOps
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink


# complete predecessor labels must agree with the source circle and active body progenitors
def ReadRimBaseTags(
    Graph: NativeGraph,
    Context: RimContext,
    Shape: CircleShape,
    Prior: GeometryState,
    Faces: dict[str, int],
    Edges: dict[str, int],
) -> tuple[FeatureTag, TopologyTags, int]:
    BodyTag = ReadRimTag(Prior, Faces["body"])
    Operation, Rounding = ReadRimOps(Graph, Context, BodyTag)
    TagSet = TopologyTags(
        ReadRimTag(Prior, Faces["side"]),
        ReadRimTag(Prior, Faces["top"]),
        ReadRimTag(Prior, Faces["bottom"]),
        ReadRimTag(Prior, Edges["top"]),
        ReadRimTag(Prior, Edges["bottom"]),
        SketchLink(CurveTag(Shape.CurveNode), 0, 0, 1, 1),
    )
    CheckRoundTags(Graph, Context.Extrusion, Shape, Operation, TagSet)
    return BodyTag, TagSet, Rounding
