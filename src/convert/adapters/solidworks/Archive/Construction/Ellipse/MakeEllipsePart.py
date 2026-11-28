from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import (
    BlindEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePart import (
    EllipsePart,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    EllipsePlan,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.EmitEllipsePart import (
    EmitEllipsePart,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.MakeEllipProf import (
    MakeEllipProf,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.ProjectEllipse import (
    ProjectEllipse,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeBlindMut import (
    MakeBlindMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import (
    MakePartHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from interchange.document.Models.DocumentModel import CadDocument


# the single ellipse boss must use the ordinary depth owner and one genuine part allocation sequence
def MakeEllipsePart(
    DocumentValue: CadDocument, InputValue: PartBuildInput
) -> EllipsePart:
    return MakeEllipPlan(DocumentValue, InputValue, ProjectEllipse(DocumentValue))


# both authored and verified readback plans use the same parametric graph allocator and emitters
def MakeEllipPlan(
    DocumentValue: CadDocument, InputValue: PartBuildInput, PlanValue: EllipsePlan
) -> EllipsePart:
    CheckPartInput(DocumentValue, InputValue, PlanValue)
    Allocator = PersistentIds()
    SystemValue = MakePartBaseMut(InputValue, PlanValue, Allocator)
    ProfileValue = MakeEllipProf(
        SystemValue, PlanValue, InputValue.TargetValue, Allocator
    )
    BossValue = MakeBlindMut(
        PlanValue.FeatureName,
        SystemValue.RootValue,
        ProfileValue,
        BlindEndInput(PlanValue.DepthValue, False, 19000),
        InputValue.TargetValue,
        Allocator,
        InputValue.DesignIntent,
        InputValue.SelectedLeader,
    )
    SetCfgStampMut(SystemValue.ConfigValues[0], Allocator)
    SystemValue.ManagerValue.FieldsValue["f658"] = 1
    HeadersValue = MakePartHeaders(SystemValue, InputValue, Allocator)
    RootsValue = (
        *SystemValue.FeatureValues,
        ProfileValue.ProfileValue,
        BossValue.FeatureValue,
    )
    return EmitEllipsePart(SystemValue, RootsValue, HeadersValue, InputValue, PlanValue)
