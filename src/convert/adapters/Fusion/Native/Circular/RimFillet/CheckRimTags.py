from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair


# the resulting round owns its new face while inherited body cap side and sketch rim labels stay unchanged
def CheckRimTags(
    Graph: NativeGraph,
    Context: RimContext,
    State: GeometryState,
    Faces: dict[str, int],
    Edges: dict[str, int],
    BodyTag: FeatureTag,
    TagSet: TopologyTags,
    Rounding: int,
) -> None:
    Table = ResolveField(Graph, Context.Feature, "rProgenitorTable", "ProgenitorTable")
    Pairs = SeriesItems(Table.Fields["ProgenitorTagVec"])
    if len(Pairs) != 1 or not isinstance(Pairs[0], ValuePair):
        raise ValueError("Native rim has unaccounted blend progenitors")
    Progenitor = Graph.Resolve(Pairs[0].First)
    if Progenitor.ClassName != "BrepProgenitor":
        raise ValueError("Native rim blend has another progenitor kind")
    Expected = {
        Faces["body"]: (BodyTag,),
        Faces["side"]: (TagSet.SideFace,),
        Faces["top"]: (TagSet.TopFace,),
        Faces["bottom"]: (TagSet.BottomFace,),
        Edges["bottom"]: (TagSet.BottomEdge,),
        Faces["blend"]: (
            FeatureTag(str(IntegerValue(Pairs[0].Second)), (Rounding,), 0, 0),
        ),
    }
    Actual = {
        Entity.Links.OwnerRef: Entity.Groups
        for Entity in State.Entities
        if isinstance(Entity, TagAttrib)
    }
    if Actual != Expected:
        raise ValueError(
            "Native rim physical labels disagree with the source operations"
        )
