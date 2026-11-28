from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
    RequireRecord,
)


# a resolved planar selection must retain its actual inherited occurrence object
def ReadChain(ModelNode: ArchiveNode, TargetNode: ArchiveNode) -> ArchiveNode:
    Chain = RequireNode(TargetNode.FieldsValue.get("f58"), "moChainComponent_c")
    if Chain.FieldsValue.get("owner") is not ModelNode:
        raise ValueError("planar mate reference chain belongs to a different assembly")
    PathNode = RequireNode(Chain.FieldsValue.get("f20"), "moReferenceChain_c")
    ListNode = RequireNode(PathNode.FieldsValue.get("f08"), "moExtFeatureList_c")
    Records = ReadRows(ListNode.FieldsValue.get("f08"))
    if len(Records) != 1:
        raise ValueError("planar mate projection requires a direct occurrence chain")
    LinkNode = RequireNode(Records[0].get("o"), "moExtFeature_c")
    Occurrence = RequireNode(LinkNode.FieldsValue.get("f50"), "moReference_c")
    OccurrenceList = RequireRecord(ModelNode.FieldsValue.get("f68"))
    ListFields = RequireRecord(OccurrenceList.get("list"))
    Members = ReadRows(ListFields.get("items"))
    if (
        Occurrence.FieldsValue.get("f4f8") is not LinkNode
        or FieldInt(LinkNode.FieldsValue, "f44")
        != FieldInt(Occurrence.FieldsValue, "f08")
        or not any(ItemValue.get("o") is Occurrence for ItemValue in Members)
    ):
        raise ValueError("resolved mate plane lost its occurrence identity")
    return Occurrence
