from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# perpendicular internal alignment and solve codes must remain distinct from unrelated external api enum numbers
def ReadMateState(NodeValue: ArchiveNode) -> Mapping[str, object]:
    if NodeValue.ClassValue.NameValue != "moMatePerpendicular":
        return {}
    return {
        "native_internal_alignment_code": FieldInt(NodeValue.FieldsValue, "f3b4"),
        "native_solved_state_code": FieldInt(NodeValue.FieldsValue, "f3b8"),
    }
