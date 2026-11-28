from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.CheckRectVisual import (
    CheckRectVisual,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.CheckSelfVisual import (
    CheckSelfVisual,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ReadChain import ReadChain


# the planar scope binds the same complete child and two actual ordered mate owners as its disclosed visibility evidence
def CheckPlanarView(
    StateValue: AssemblyState,
    ChildValue: PartCandidate,
    References: tuple[ArchiveNode, ...],
    MateRoots: tuple[ArchiveNode, ...],
) -> None:
    CheckRectVisual(ChildValue.PlanValue)
    CheckSelfVisual(ChildValue)
    Count = len(References)
    FirstClass = "moMateCoincident" if Count == 2 else "moMateParallel"
    Group = RequireNode(StateValue.GroupValue, "moMateGroup_c")
    if (
        Count not in (2, 3)
        or tuple(MateValue.ClassValue for MateValue in MateRoots)
        != (RuntimeClass(FirstClass, 1), RuntimeClass("moMateDistanceDim_c", 1))
        or Group not in StateValue.FeatureValues
        or Group.FieldsValue["owner"] is not StateValue.RootValue
        or any(MateValue.FieldsValue["owner"] is not Group for MateValue in MateRoots)
        or FieldInt(MateRoots[0].FieldsValue, "f08")
        >= FieldInt(MateRoots[1].FieldsValue, "f08")
    ):
        raise ValueError(
            "planar visibility requires the actual ordered aligned and distance mates"
        )
    for MateValue, Moving in zip(
        MateRoots, (References[1], References[-1]), strict=True
    ):
        Endpoints = tuple(
            ReadChain(
                StateValue.RootValue,
                RequireNode(
                    RequireNode(RowValue["o"], "moPlaneRef_w").FieldsValue["f58"],
                    "moCompRefPlane_c",
                ),
            )
            for RowValue in ReadRows(MateValue.FieldsValue["f410"])
        )
        if Endpoints != (References[0], Moving):
            raise ValueError("planar visibility lost the actual ordered mate endpoints")
