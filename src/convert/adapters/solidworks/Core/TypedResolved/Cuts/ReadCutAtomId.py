from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


# an archive atom must retain its actual solid producer in both feature identity fields
def ReadCutAtomId(AtomValue: ArchiveNode, FeatureValue: ArchiveNode) -> int:
    Fields = AtomValue.FieldsValue
    AtomId = Fields.get("f140")
    FeatureId = NativeNodeId(FeatureValue)
    if (
        type(AtomId) is not int
        or AtomId <= 0
        or Fields.get("body_kind") != 0
        or Fields.get("f12c") != FeatureId
        or Fields.get("f130") != FeatureId
    ):
        raise ValueError("cut atom identity does not agree with its solid producer")
    return AtomId
