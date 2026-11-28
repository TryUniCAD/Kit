from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.LookResource import (
    LookResource,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.MakeBasicPbr import (
    MakeBasicPbr,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.MakeRealView import (
    MakeRealView,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PackLookRgb import (
    PackLookRgb,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PartLookInput import (
    PartLookInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PlanLookIds import (
    PlanLookIds,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.MakeMaterial import (
    MakeMaterial,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.MakeModelVisual import (
    MakeModelVisual,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# each visual owner holds a fresh shader graph with its own publication identity and resource spelling
def MakeRenderLook(InputValue: PartLookInput, *, Holder: bool) -> ArchiveNode:
    if type(InputValue) is not PartLookInput or InputValue.LegacyMaterialName not in (
        "",
        "Steel",
    ):
        raise ValueError(
            "part rendering requires the unassigned legacy material label profile"
        )
    SpecularValue = RequireScalar(InputValue.LegacySpecular)
    if not 0.0 <= SpecularValue <= 1.0:
        raise ValueError("part rendering legacy specular must be normalized")
    HolderId, LiveId, _ = PlanLookIds(InputValue)
    ResourceValue = LookResource(InputValue, Holder=Holder)
    ColorValue = PackLookRgb(InputValue.MainRgb)
    MaterialValue = MakeMaterial()
    MaterialValue.update(
        f20=InputValue.LegacyMaterialName,
        f48=SpecularValue,
        has90=1,
        f90=MakeRealView(
            InputValue.ClassicValue,
            HolderId if Holder else LiveId,
            ResourceValue,
            ColorValue,
        ),
    )
    VisualValue = MakeModelVisual()
    VisualValue.FieldsValue.update(
        f0c=ColorValue,
        f18=PackLookRgb(InputValue.HiddenLineRgb),
        f20=MaterialValue,
        has88=1,
        f88=MakeBasicPbr(InputValue.ShaderValue),
    )
    return VisualValue
