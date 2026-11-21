from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
    RequireRecord,
)


# direct mate chains must reuse the containing assembly occurrence and its existing external feature backlink
def MakeMateChain(Assembly: ArchiveNode, Occurrence: ArchiveNode) -> ArchiveNode:
    _ = RequireNode(Assembly, "moAssembly_c")
    _ = RequireNode(Occurrence, "moReference_c")
    Members = ReadRows(
        RequireRecord(RequireRecord(Assembly.FieldsValue.get("f68")).get("list")).get(
            "items"
        )
    )
    if (
        not any(Value.get("o") is Occurrence for Value in Members)
        or Occurrence.FieldsValue.get("owner") is not Assembly
    ):
        raise ValueError(
            "mate occurrence must belong to the actual containing assembly"
        )
    External = RequireNode(Occurrence.FieldsValue.get("f4f8"), "moExtFeature_c")
    if External.FieldsValue.get("f50") is not Occurrence or FieldInt(
        External.FieldsValue, "f44"
    ) != FieldInt(Occurrence.FieldsValue, "f08"):
        raise ValueError("mate occurrence external entry lost its actual backlink")
    FeatureList = ArchiveNode(
        RuntimeClass("moExtFeatureList_c", 1), {"n": 1, "f08": [{"o": External}]}
    )
    ChainValue = ArchiveNode(
        RuntimeClass("moReferenceChain_c", 1),
        {"f08": FeatureList, "f20": 0, "f24": 0, "f40": {"f08": "", "f10": -1}},
    )
    return ArchiveNode(
        RuntimeClass("moChainComponent_c", 1),
        {
            "owner": Assembly,
            "f20": ChainValue,
            "f30": (101 + FieldInt(Occurrence.FieldsValue, "f3f0")) & 0xFFFFFFFF,
        },
    )
