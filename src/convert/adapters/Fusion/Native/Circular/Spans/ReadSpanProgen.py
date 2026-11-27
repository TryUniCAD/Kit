from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    RequireFields,
    ResolveField,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    MappingItems,
    ObjectFields,
    SeriesItems,
)
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair


# live progenitor occurrences select active operations without discarding unused allocated identities
def ReadSpanProgen(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    BodyTag: FeatureTag,
    AllocatedIds: tuple[int, ...],
) -> tuple[int, ...]:
    Operation = int(BodyTag.PrimaryId)
    Table = ResolveField(Graph, Context.Extrude, "rProgenitorTable", "ProgenitorTable")
    Entries = SeriesItems(Table.Fields["ProgenitorTagVec"])
    if len(Entries) != 2 or any(not isinstance(Entry, ValuePair) for Entry in Entries):
        raise ValueError("Native circular span has unaccounted progenitors")
    BodyPairs = tuple(
        Entry
        for Entry in Entries
        if isinstance(Entry, ValuePair)
        and Graph.Resolve(Entry.First).ClassName == "BodyProgenitor"
    )
    if len(BodyPairs) != 1 or BodyTag != FeatureTag(
        str(Operation), (), IntegerValue(BodyPairs[0].Second), 0
    ):
        raise ValueError("Native circular span body tag disagrees with its progenitor")
    Progenitor = Graph.Resolve(BodyPairs[0].First)
    RequireFields(
        Progenitor,
        {
            "alternativeProgenitor": None,
            "rRefBodyOfTagInherit": None,
            "shareTargetBodyAddress": False,
            "centerOrder": 0,
        },
    )
    Occurrences = MappingItems(Progenitor.Fields["featureTagOccMap"])
    ActiveIds = {
        IntegerValue(ObjectFields(Entry.First)["operationId"]) for Entry in Occurrences
    }
    OwnedIds = AllocatedIds
    Operations = tuple(Value for Value in OwnedIds if Value in ActiveIds)
    if (
        not Operations
        or Operations[0] != Operation
        or not ActiveIds <= set(OwnedIds)
        or len(set(Operations)) != len(Operations)
    ):
        raise ValueError("Native circular span operation order disagrees with its body")
    Curves = tuple(
        Entry
        for Entry in Entries
        if isinstance(Entry, ValuePair)
        and Graph.Resolve(Entry.First).ClassName == "SketchCurveProgenitor"
    )
    if len(Curves) != 1:
        raise ValueError("Native circular span has no unique source curve progenitor")
    Encoded = tuple(str(IntegerValue(Curves[0].Second)).encode("ascii"))
    Fields = tuple(ObjectFields(Entry.First) for Entry in Occurrences)
    if (
        Progenitor.Fields["bodyUuid"] != Context.DcBody.Fields["bodyUuid"]
        or len(Occurrences) != len(Operations)
        or {Value["operationId"] for Value in Fields} != set(Operations)
        or any(Entry.Second != 1 for Entry in Occurrences)
        or any(
            Value["primary"] is not False
            or SeriesItems(Value["facePrimIdData"]) != Encoded
            or SeriesItems(Value["facePrimIdOffsets"]) != (0, len(Encoded))
            for Value in Fields
        )
    ):
        raise ValueError("Native circular span progenitor belongs to another operation")
    SketchTable = ResolveField(
        Graph, Context.SketchFeature, "rProgenitorTable", "ProgenitorTable"
    )
    EmptyFields(SketchTable, ("ProgenitorTagVec",))
    return Operations
