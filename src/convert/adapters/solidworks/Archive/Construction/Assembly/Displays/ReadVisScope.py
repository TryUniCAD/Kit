from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    ReadRows,
    RequireNode,
    RequireRecord,
)


# both visibility profiles must join the actual selected configuration and ordered direct occurrences
def ReadVisScope(
    StateValue: AssemblyState,
    ChildValue: PartCandidate,
    References: tuple[ArchiveNode, ...],
) -> tuple[ArchiveNode, tuple[str, ...], tuple[int, ...]]:
    Manager = RequireNode(StateValue.ManagerValue, "moConfigurationMgr_c").FieldsValue
    Config = RequireNode(StateValue.CurrentConfig, "moConfiguration_c")
    ConfigTable = RequireRecord(Manager["f370"])
    ConfigRows = ReadRows(ConfigTable["items"])
    if (
        Manager.get("f1f8") != ""
        or FieldInt(ConfigTable, "n") != 1
        or len(ConfigRows) != 1
        or any(
            Value is not Config
            for Value in (Manager["f360"], Manager["f368"], ConfigRows[0]["o"])
        )
        or FieldInt(Config.FieldsValue, "f08") < 0
    ):
        raise ValueError(
            "assembly visibility requires one selected configuration and the fresh empty manager locator"
        )
    RootFields = RequireNode(StateValue.RootValue, "moAssembly_c").FieldsValue
    Table = RequireRecord(RequireRecord(RootFields["f68"])["list"])
    Actual = tuple(
        RequireNode(RowValue["o"], "moReference_c")
        for RowValue in ReadRows(Table["items"])
    )
    Count = len(References)
    if Count not in (2, 3) or FieldInt(Table, "n") != Count or Actual != References:
        raise ValueError(
            "assembly visibility requires the actual ordered direct occurrences"
        )
    Directory = RequireNode(Actual[0].FieldsValue["f3b0"], "moExtObject_c")
    ChildFile = RequireNode(ChildValue.TopHeader.FieldsValue["f38"], "moExtObject_c")
    if (
        ReadFileKey(Directory) != ReadFileKey(ChildFile)
        or ReadFileKey(Directory)[2] != 2
        or tuple(FieldInt(NodeValue.FieldsValue, "f408") for NodeValue in Actual)
        != (1,) + (0,) * (Count - 1)
        or any(
            NodeValue.FieldsValue["f3b0"] is not Directory
            or NodeValue.FieldsValue["hidden"] != 0
            for NodeValue in Actual
        )
    ):
        raise ValueError(
            "assembly visibility requires the shared visible child and the actual fixed occurrence"
        )
    Names = tuple(ReadNodeName(NodeValue) for NodeValue in Actual)
    FeatureIds = tuple(FieldInt(NodeValue.FieldsValue, "f08") for NodeValue in Actual)
    if (
        len({NameValue.casefold() for NameValue in Names}) != Count
        or len(set(FeatureIds)) != Count
        or min(FeatureIds) <= 0
    ):
        raise ValueError("assembly visibility occurrence identities are ambiguous")
    return Config, Names, FeatureIds
