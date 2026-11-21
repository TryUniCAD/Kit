from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.MakeRenderLook import (
    MakeRenderLook,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PartLookInput import (
    PartLookInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PlanLookIds import (
    PlanLookIds,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.MakeModelVisual import (
    MakeModelVisual,
)
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.MakeEmptyMgrs import (
    MakeEmptyMgrs,
)
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.ReadEmptyMgrs import (
    ReadEmptyMgrs,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode


# renderer publication updates only fresh model configuration and definition owners after computing the complete graph
def PutRenderMut(
    ModelValue: ArchiveNode,
    ConfigValue: ArchiveNode,
    Definition: ModelDefGraph,
    InputValue: PartLookInput,
) -> None:
    ModelLook = RequireNode(ModelValue.FieldsValue["f78"], "moVisualProperties_c")
    DefinitionFields = Definition.DocumentValue.FieldsValue
    PriorManagers = ReadEmptyMgrs(Definition)
    if (
        ConfigValue.FieldsValue["owner"] is not ModelValue
        or ConfigValue.FieldsValue["f78"] is not None
        or ModelLook.FieldsValue != MakeModelVisual().FieldsValue
        or PriorManagers.AppearanceValue.ManagerOnWire
        or PriorManagers.BomOnWire
    ):
        raise ValueError(
            "part rendering may publish only at fresh unowned document slots"
        )
    NewModel = MakeRenderLook(InputValue, Holder=False)
    NewConfig = MakeRenderLook(InputValue, Holder=False)
    _, _, NextState = PlanLookIds(InputValue)
    DefinitionFields.update(MakeEmptyMgrs(NextState))
    ModelValue.FieldsValue["f78"] = NewModel
    ConfigValue.FieldsValue["f78"] = NewConfig
