from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import (
    AsmDisplayIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.ReadDisplayRows import (
    ReadDisplayRows,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.VisualStates.WriteAsmVisual import (
    KVisualStream,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    ReadRows,
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ReadChain import ReadChain


# visibility must bind the actual measured generated component scope before allocating store objects
def CheckAsmDisplay(
    StateValue: AssemblyState,
    ChildValue: PartCandidate,
    References: tuple[ArchiveNode, ...],
    MateRoots: tuple[ArchiveNode, ...],
    DisplayValues: tuple[AsmDisplayIn, ...],
) -> tuple[ArchiveNode, tuple[tuple[str, dict[int, bool]], ...]]:
    PlanValue = ChildValue.PlanValue
    if (
        type(PlanValue) is not CirclePlan
        or PlanValue.AxisValue != "z"
        or PlanValue.IsDiameter
        or PlanValue.EndValue.ModeValue != "blind"
        or PlanValue.EndValue.IsReversed
        or KVisualStream in ChildValue.StreamsValue
    ):
        raise ValueError(
            "assembly visibility requires the ordinary radial child without a visual store"
        )
    if (
        len(MateRoots) != 1
        or MateRoots[0].ClassValue != RuntimeClass("moMateConcentric", 1)
        or MateRoots[0].FieldsValue.get("owner") is not StateValue.GroupValue
        or MateRoots[0].FieldsValue.get("f3b4") != 1
        or MateRoots[0].FieldsValue.get("f4b8") != 0
    ):
        raise ValueError(
            "assembly visibility requires one actual aligned unlocked concentric mate"
        )
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
    if (
        FieldInt(Table, "n") != 2
        or len(Actual) != 2
        or len(References) != 2
        or any(
            LeftValue is not RightValue
            for LeftValue, RightValue in zip(Actual, References, strict=True)
        )
    ):
        raise ValueError(
            "assembly visibility requires the two actual direct occurrences"
        )
    Selected = tuple(
        ReadChain(
            StateValue.RootValue,
            RequireNode(
                RequireNode(RowValue["o"], "moCylinderRef_w").FieldsValue["f58"],
                "moCompFace_c",
            ),
        )
        for RowValue in ReadRows(MateRoots[0].FieldsValue["f410"])
    )
    if Selected != Actual:
        raise ValueError(
            "assembly visibility requires both actual ordered concentric endpoints"
        )
    Directory = RequireNode(Actual[0].FieldsValue["f3b0"], "moExtObject_c")
    ChildFile = RequireNode(ChildValue.TopHeader.FieldsValue["f38"], "moExtObject_c")
    if (
        ReadFileKey(Directory) != ReadFileKey(ChildFile)
        or ReadFileKey(Directory)[2] != 2
        or tuple(FieldInt(NodeValue.FieldsValue, "f408") for NodeValue in Actual)
        != (1, 0)
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
        len({NameValue.casefold() for NameValue in Names}) != 2
        or len(set(FeatureIds)) != 2
        or min(FeatureIds) <= 0
    ):
        raise ValueError("assembly visibility occurrence identities are ambiguous")
    return Config, ReadDisplayRows(DisplayValues, Names, FeatureIds)
