from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import (
    AsmDisplayIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.CheckCylSelfVis import (
    CheckCylSelfVis,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.CheckPlanarView import (
    CheckPlanarView,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.ReadDisplayRows import (
    ReadDisplayRows,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.ReadVisScope import (
    ReadVisScope,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    ReadRows,
    RequireNode,
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
    if type(PlanValue) is BlindPlan:
        CheckPlanarView(StateValue, ChildValue, References, MateRoots)
        Config, Names, FeatureIds = ReadVisScope(StateValue, ChildValue, References)
        return Config, ReadDisplayRows(DisplayValues, Names, FeatureIds, Planar=True)
    if (
        type(PlanValue) is not CirclePlan
        or PlanValue.AxisValue != "z"
        or PlanValue.IsDiameter
        or PlanValue.EndValue.ModeValue != "blind"
        or PlanValue.EndValue.IsReversed
    ):
        raise ValueError(
            "assembly visibility requires the ordinary radial child without a visual store"
        )
    CheckCylSelfVis(ChildValue, DisplayValues)
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
    if len(References) != 2:
        raise ValueError(
            "assembly visibility requires the two actual direct occurrences"
        )
    Config, Names, FeatureIds = ReadVisScope(StateValue, ChildValue, References)
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
    if Selected != References:
        raise ValueError(
            "assembly visibility requires both actual ordered concentric endpoints"
        )
    return Config, ReadDisplayRows(DisplayValues, Names, FeatureIds)
