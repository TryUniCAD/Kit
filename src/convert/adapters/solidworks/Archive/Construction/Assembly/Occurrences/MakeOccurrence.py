from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeExtFeature import (
    MakeExtFeature,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakePlacement import (
    MakePlacement,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.System.MakeAsmNode import (
    MakeAsmNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.FieldRecord import (
    FieldRecord,
)
from convert.adapters.solidworks.Archive.Construction.System.ClearSystemMut import (
    ClearSystemMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName


# ordinary resolved occurrences derive target configuration updates bounds and containing file backlinks from their actual generated definitions
def MakeOccurrence(
    StateValue: AssemblyState,
    ChildValue: PartCandidate,
    Directory: ArchiveNode,
    OwnerFile: ArchiveNode,
    InputValue: OccurrenceIn,
    TargetValue: FeatureTarget,
    BoundsValue: dict[str, float],
    OrdinalValue: int,
) -> ArchiveNode:
    NodeValue = MakeAsmNode(
        "moReference_c",
        InputValue.NameValue,
        StateValue.RootValue,
        TargetValue,
        StateValue.Allocator,
    )
    FieldsValue = NodeValue.FieldsValue
    FieldsValue.update(
        dict.fromkeys(
            (
                "has_discarded_xform",
                "has_f378",
                "f388",
                "f408",
                "f418",
                "f41c",
                "f450",
                "f454",
                "f458",
                "f49c",
                "f4a0",
                "f4c0",
                "f4d8",
                "f4dc",
                "f4f0",
                "f524",
                "f530",
                "f550",
                "f368",
            ),
            0,
        )
    )
    FieldsValue.update(
        dict.fromkeys(
            ("f468", "f470", "f488", "f490", "f538", "f548", "discarded_stack"), None
        )
    )
    FieldsValue.update(
        {
            "f3e0": ChildValue.HeaderValue.FieldsValue["f40"],
            "f3e8": ChildValue.HeaderValue.FieldsValue["f48"],
            "f3f4": ChildValue.SystemValue.RootValue.FieldsValue["f1300"],
            "f3f0": 102,
            "f3f8": 101,
        }
    )
    FieldsValue.update(
        {
            "has_f360": 1,
            "f360": MakePlacement(InputValue.FrameValue),
            "has_f370": 1,
            "f370": dict(BoundsValue),
            "f3b0": Directory,
            "f3c0": {
                "f08": ReadNodeName(ChildValue.CurrentConfig),
                "f10": ChildValue.CurrentConfig.FieldsValue["f08"],
            },
            "f3dc": -1,
            "f400": 3,
            "f4a4": -1,
            "f4b0": -1,
            "f4b4": OrdinalValue,
            "f500": "",
            "f508": "",
            "f55c": 101,
        }
    )
    FieldsValue["f4f8"] = MakeExtFeature(
        NodeValue, FieldRecord(OwnerFile.FieldsValue["shared"]), True
    )
    ClearSystemMut(NodeValue)
    return NodeValue
