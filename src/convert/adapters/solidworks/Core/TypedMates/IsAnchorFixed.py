from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireNode,
)


# persisted lightweight references retain their actual identity through body membership and external backlinks while live owner pointers may be absent
def IsAnchorFixed(NodeValue: ArchiveNode, ExpectedName: str) -> bool:
    External = RequireNode(NodeValue.FieldsValue["f4f8"], "moExtFeature_c")
    FixedValue = FieldInt(NodeValue.FieldsValue, "f408")
    if (
        ReadNodeName(NodeValue) != ExpectedName
        or External.FieldsValue.get("f50") is not NodeValue
        or FieldInt(External.FieldsValue, "f44")
        != FieldInt(NodeValue.FieldsValue, "f08")
        or FixedValue not in (0, 1)
    ):
        raise ValueError("typed occurrence anchor identity or boolean flag differs")
    return bool(FixedValue)
