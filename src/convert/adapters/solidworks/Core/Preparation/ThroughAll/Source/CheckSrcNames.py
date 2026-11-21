from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadRows
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceTree import (
    ReadSourceTree,
)
from interchange.document.Models.DocumentModel import CadDocument


# retained presentation identity alone cannot qualify a source whose actual public names have diverged from its owner evidence
def CheckSrcNames(DocumentValue: CadDocument) -> None:
    TreeValue = ReadSourceTree(DocumentValue)
    RowsValue = ReadRows(TreeValue.get("rows"))
    NamesValue = {
        Value.get("native_object_id"): Value.get("name") for Value in RowsValue
    }
    HelpersValue = ReadRows(TreeValue.get("configuration_helpers"))
    HelperIds = {Value.get("stored_node_id") for Value in HelpersValue}
    PublicIds = {
        Value.attributes.get("native_object_id")
        for Value in DocumentValue.feature_timeline
    }
    if (
        set(NamesValue).intersection(HelperIds)
        or set(NamesValue).union(HelperIds) != PublicIds
    ):
        raise ValueError(
            "source presentation no longer covers every actual public owner"
        )
    if any(
        Value.name != NamesValue[Value.attributes.get("native_object_id")]
        for Value in DocumentValue.feature_timeline
        if Value.attributes.get("native_object_id") not in HelperIds
    ):
        raise ValueError("source presentation names are stale or foreign")
