from convert.adapters.solidworks.Archive.Construction.Circles.AddCircDimMut import (
    AddCircDimMut,
)
from convert.adapters.solidworks.Archive.Construction.Circles.MakeCircleFeat import (
    MakeCircleFeat,
)
from convert.adapters.solidworks.Archive.Construction.Circles.RadialLabelIn import (
    RadialLabelIn,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import (
    FinishBlindMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import (
    ProjectCircle,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import (
    MakeSketchKeys,
)
from interchange.document.Models.DocumentModel import CadDocument


# the analytic profile and its actual driver join the same allocation and complete part stream composition as the line loop
def MakeCirclePart(
    DocumentValue: CadDocument,
    InputValue: PartBuildInput,
    *,
    LabelValue: RadialLabelIn | None = None,
) -> PartCandidate:
    PlanValue = ProjectCircle(DocumentValue)
    CheckPartInput(DocumentValue, InputValue, PlanValue)
    FirstValue, SecondValue = PlanValue.TextPoint
    NormalOffset = 0.0
    if LabelValue is not None:
        if (
            type(LabelValue) is not RadialLabelIn
            or LabelValue.SketchId != PlanValue.SketchId
            or LabelValue.ParameterId != PlanValue.RadialId
        ):
            raise ValueError(
                "radial label requires its actual owned sketch and radial driver"
            )
        FirstValue, SecondValue, NormalOffset = LabelValue.TextPoint
    Allocator = PersistentIds()
    SystemValue = MakePartBaseMut(InputValue, PlanValue, Allocator)
    ProfileValue = MakeCircleFeat(
        PlanValue.SketchName,
        SystemValue.RootValue,
        SystemValue.SystemValues.PlaneValues[PlanValue.AxisValue],
        PlanValue.AxisValue,
        PlanValue.CircleValue,
        InputValue.TargetValue,
        Allocator,
    )
    Dimension = AddCircDimMut(
        ProfileValue,
        (FirstValue, SecondValue),
        PlanValue.IsDiameter,
        InputValue.DesignIntent,
        InputValue.SelectedLeader,
        Allocator,
        NormalOffset=NormalOffset,
    )
    return FinishBlindMut(
        SystemValue,
        ProfileValue,
        InputValue,
        PlanValue,
        Allocator,
        MakeSketchKeys((Dimension,), InputValue.DocumentUnits.LengthUnit),
    )
