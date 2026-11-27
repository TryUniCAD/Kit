from convert.adapters.Fusion.Native.Graph.GraphChecks import RequireFields
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    MappingItems,
    ObjectFields,
    SeriesItems,
)
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag


# stock body occurrences must identify the same side labels and operation as their native source recipes
def CheckStockTags(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Labels: dict[int, FeatureTag],
    Operation: int,
) -> None:
    Progenitor = Graph.OneClass("BodyProgenitor")
    RequireFields(
        Progenitor,
        {
            "alternativeProgenitor": None,
            "rRefBodyOfTagInherit": None,
            "shareTargetBodyAddress": False,
            "centerOrder": 0,
            "bodyUuid": Context.DcBody.Fields["bodyUuid"],
        },
    )
    Occurrences = MappingItems(Progenitor.Fields["featureTagOccMap"])
    if len(Occurrences) != 1 or Occurrences[0].Second != 1:
        raise ValueError("Native cut stock has an ambiguous body occurrence")
    Fields = ObjectFields(Occurrences[0].First)
    Encoded = tuple(Value.PrimaryId.encode("ascii") for Value in Labels.values())
    Offsets = tuple(
        sum(len(Value) for Value in Encoded[:Index])
        for Index in range(len(Encoded) + 1)
    )
    if (
        Fields["primary"] is not False
        or IntegerValue(Fields["operationId"]) != Operation
        or SeriesItems(Fields["facePrimIdData"]) != tuple(b"".join(Encoded))
        or SeriesItems(Fields["facePrimIdOffsets"]) != Offsets
    ):
        raise ValueError(
            "Native cut body occurrence disagrees with its stock side identities"
        )
