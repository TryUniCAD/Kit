from convert.adapters.solidworks.Archive.Construction.Presentation.MakeModelVisual import (
    MakeModelVisual,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.MakeRenderLook import (
    MakeRenderLook,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PartLookInput import (
    PartLookInput,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    RequireNode,
    RequireRecord,
)


# the initial part update allocates an independent selected appearance from the real model constructor
def BindSelfLookMut(Config: ArchiveNode) -> None:
    if Config.FieldsValue["f78"] is not None:
        raise ValueError(
            "part self visibility cannot replace a supplied configuration appearance"
        )
    Config.FieldsValue["f78"] = MakeModelVisual()


# part self appearance owns a distinct visual record and must refuse an unmodeled renderer
def MakeHolderLook(
    RootValue: ArchiveNode, Config: ArchiveNode, RenderValue: PartLookInput | None
) -> ArchiveNode:
    ModelVisual = RequireNode(RootValue.FieldsValue["f78"], "moVisualProperties_c")
    ConfigVisual = RequireNode(Config.FieldsValue["f78"], "moVisualProperties_c")
    ModelMaterial = RequireRecord(ModelVisual.FieldsValue["f20"])
    ConfigMaterial = RequireRecord(ConfigVisual.FieldsValue["f20"])
    if RenderValue is None and any(
        Visual.FieldsValue.get("has88") != 0 or Material.get("has90") != 0
        for Visual, Material in (
            (ModelVisual, ModelMaterial),
            (ConfigVisual, ConfigMaterial),
        )
    ):
        raise ValueError(
            "part self visibility cannot project populated RealView or DSPBR appearance"
        )
    LiveValue = (
        MakeModelVisual()
        if RenderValue is None
        else MakeRenderLook(RenderValue, Holder=False)
    )
    if (
        ModelVisual is ConfigVisual
        or ModelMaterial is ConfigMaterial
        or ModelVisual.FieldsValue != LiveValue.FieldsValue
        or ConfigVisual.FieldsValue != LiveValue.FieldsValue
    ):
        if RenderValue is not None:
            raise ValueError(
                "part self visibility lost the actual live renderer owners"
            )
        raise ValueError(
            "part self visibility requires two actual constructor appearance owners"
        )
    if RenderValue is not None and (
        ModelMaterial["f90"] is ConfigMaterial["f90"]
        or ModelVisual.FieldsValue["f88"] is ConfigVisual.FieldsValue["f88"]
    ):
        raise ValueError("part self visibility lost the actual live renderer owners")
    return (
        MakeModelVisual()
        if RenderValue is None
        else MakeRenderLook(RenderValue, Holder=True)
    )
