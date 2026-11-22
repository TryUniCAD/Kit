from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Core.Native import NativeFeatureA, NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# the complete cold history may contain only ordered ordinary roots and empty system owners
def CheckColdRows(
    Model: NativeModel, LinkValue: NativeLink, Features: Mapping[int, ArchiveNode]
) -> None:
    FieldsValue = LinkValue.ConfigValue.RootValue.FieldsValue
    PublicIds = tuple(Value.object_id for Value in Model.features)
    if (
        FieldsValue.get("f1014") != 0
        or FieldsValue.get("f1018") is not None
        or FieldsValue.get("f13f8") is not None
        or len(Features) != 23
        or len(PublicIds) != 23
        or set(PublicIds) != set(Features)
        or Model.features != tuple(sorted(Model.features, key=NativeFeatureA))
        or any(
            RowValue.name != ReadNodeName(Features[RowValue.object_id])
            for RowValue in Model.features
        )
    ):
        raise ValueError("cold two-stock presentation has alternate owners")
    for NodeValue in Features.values():
        Fields = NodeValue.FieldsValue
        ClassName = NodeValue.ClassValue.NameValue
        if (
            Fields.get("f2b0") != 19000
            or Fields.get("f0c") not in (0, 1)
            or Fields.get("f2c") != 0
            or Fields.get("has_list68") != 0
            or Fields.get("f78") is not None
        ):
            raise ValueError("cold two-stock feature retains unsupported state")
        if ClassName in ("moDetailCabinet_c", "moEnvFolder_c") and not all(
            IsLineState(Fields[FieldName])
            for FieldName in ("f60", "f368", "f388")
            if FieldName in Fields
        ):
            raise ValueError("cold two-stock presentation has persisted children")
