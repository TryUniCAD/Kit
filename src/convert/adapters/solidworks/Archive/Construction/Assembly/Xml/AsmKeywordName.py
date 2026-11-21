from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName


# the native keyword index represents the nameless config manager with an explicit empty name
def AsmKeywordName(NodeValue: ArchiveNode) -> str:
    if NodeValue.ClassValue.NameValue == "moExplViewManager_c":
        if (
            "f18" not in NodeValue.FieldsValue
            or NodeValue.FieldsValue["f18"] is not None
        ):
            raise ValueError(
                "ordinary assembly exploded manager cannot carry a name owner"
            )
        return ""
    return ReadNodeName(NodeValue)
