from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import (
    AsmDisplayIn,
)
from convert.adapters.solidworks.Archive.Construction.AssemblySets.OrderedAsm import (
    OrderedAsm,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylAsm import (
    MakeCylAsm,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Children.ReadAsmPlanes import (
    ReadAsmPlanes,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PlanCylMate import (
    PlanCylMate,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PrepCylChild import (
    PrepCylChild,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import (
    ReadAsmModel,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import (
    ReadAsmPaths,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.MakeAsmRecipe import (
    MakeAsmRecipe,
)
from convert.adapters.solidworks.Core.Preparation.DefaultPartTree import DefaultPartTree
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# a root without selected datum geometry can synthesize the ordinary builtin plane system
def ReadCylPlanes(
    DocumentValue: CadDocument, WrittenAt: int
) -> dict[str, SupportPlane]:
    if DocumentValue.support_planes:
        return ReadAsmPlanes(DocumentValue)
    ResultValue: dict[str, SupportPlane] = {}
    for AxisValue, NameValue in DefaultPartTree("Front Plane", WrittenAt).PlaneNames:
        FrameValue = PrincipalFrame(AxisValue)
        ResultValue[AxisValue] = SupportPlane(
            "native/principal/" + AxisValue,
            NameValue,
            Transform(
                SpaceVector(*FrameValue.OriginValue),
                SpaceVector(*FrameValue.AxisU),
                SpaceVector(*FrameValue.AxisV),
                SpaceVector(*FrameValue.NormalValue),
            ),
        )
    return ResultValue


# the parent and selected lateral faces must use the same generated child and sibling locator
def PrepCylAsm(
    DocumentValue: CadDocument,
    NativePath: str,
    WrittenAt: int,
    SceneName: str,
    LightValues: tuple[LightInput, ...],
    *,
    DisplayValues: tuple[AsmDisplayIn, ...] | None = None,
) -> OrderedAsm:
    ModelValue = ReadAsmModel(DocumentValue)
    PathsValue = ReadAsmPaths(
        ModelValue.RootValue.name, ModelValue.ChildValue.name, NativePath, WrittenAt
    )
    ChildValue = PrepCylChild(
        ModelValue.ChildDocument, PathsValue.ChildValue, SceneName, LightValues
    )
    PlanValue = PlanCylMate(
        DocumentValue,
        ModelValue.ChildDocument,
        ChildValue.CandidateValue,
        ChildValue.FaceTag,
    )
    RootRecipe = MakeAsmRecipe(
        ModelValue,
        MakePartRecipe(ChildValue.CandidateValue.PlanValue, WrittenAt),
        ReadCylPlanes(DocumentValue, WrittenAt),
        PathsValue.ParentValue,
    )
    return MakeCylAsm(
        PlanValue.CandidateValue,
        RootRecipe,
        PlanValue.Placements,
        PlanValue.EndIndexes,
        PlanValue.FaceValue.FaceTag,
        PlanValue.MateInput,
        DisplayValues=DisplayValues,
    )
