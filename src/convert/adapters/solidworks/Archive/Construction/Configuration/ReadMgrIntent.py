from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import (
    ConfigSpec,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.ManagerInput import (
    ManagerInput,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.ReadMgrName import (
    ReadMgrName,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    FieldText,
    RequireRecord,
    ReadRows,
)


# ordinary source selectors must resolve to their actual owned configuration before constructor intent is returned
def ReadMgrIntent(ManagerValue: ArchiveNode) -> ManagerInput:
    NameValue = ReadMgrName(ManagerValue)
    FieldsValue = ManagerValue.FieldsValue
    TableValue = RequireRecord(FieldsValue.get("f370"))
    RowsValue = ReadRows(TableValue.get("items"))
    ConfigValues = tuple(
        ArchiveNode.RequireNode(RowValue.get("o")) for RowValue in RowsValue
    )
    if (
        not ConfigValues
        or FieldInt(TableValue, "n") != len(ConfigValues)
        or FieldInt(FieldsValue, "f40c") != len(ConfigValues)
    ):
        raise ValueError("ordinary manager allocation and directory counts differ")
    SpecsValue: list[ConfigSpec] = []
    for IndexValue, NodeValue in enumerate(ConfigValues):
        RequireRootNode(NodeValue, "moPartConfiguration_c")
        if FieldInt(NodeValue.FieldsValue, "f08") != IndexValue:
            raise ValueError(
                "ordinary manager requires its actual ordinal local identifiers"
            )
        NameNode = ArchiveNode.RequireNode(NodeValue.FieldsValue["f18"])
        RequireRootNode(NameNode, "moNodeName_c")
        SpecsValue.append(
            ConfigSpec(
                FieldText(NameNode.FieldsValue, "f08"),
                ReadStyleText(
                    NodeValue.FieldsValue.get("f4a8"), "configuration description"
                ),
                FieldInt(NodeValue.FieldsValue, "f678"),
            )
        )
    CurrentValue = FieldsValue.get("f360")
    MatchesValue = tuple(
        IndexValue
        for IndexValue, NodeValue in enumerate(ConfigValues)
        if NodeValue is CurrentValue
    )
    if len(MatchesValue) != 1 or FieldsValue.get("f368") is not CurrentValue:
        raise ValueError(
            "ordinary manager selectors must alias one actual directory configuration"
        )
    return ManagerInput(NameValue, tuple(SpecsValue), MatchesValue[0])
