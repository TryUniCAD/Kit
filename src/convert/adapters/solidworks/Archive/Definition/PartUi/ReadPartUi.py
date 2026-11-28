from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Definition.PartUi.PartUiInput import (
    PartUiInput,
)
from convert.adapters.solidworks.Archive.Definition.PartUi.CountPartEnvs import (
    CountPartEnvs,
)
from convert.adapters.solidworks.Archive.Definition.PartUi.RequirePartUi import (
    RequirePartUi,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# explicit source settings must match the part context normalizer and the constructor preserved grid mask
def ReadPartUi(GraphValue: ModelDefGraph) -> PartUiInput:
    FieldsValue = RequirePartUi(GraphValue)
    _ = CountPartEnvs(GraphValue)
    GridValue = FieldInt(FieldsValue, "fad4")
    ContextValue = FieldInt(FieldsValue, "fb00")
    GroupValue = FieldInt(FieldsValue, "fb04")
    if (
        FieldInt(FieldsValue, "facc") != 3
        or GridValue not in (2, 3)
        or ContextValue != 1
        or GroupValue not in (0, 0x958C)
    ):
        raise ValueError(
            "part ui grid mask or confirmed default context is unrepresented"
        )
    return PartUiInput(
        FieldInt(FieldsValue, "fad0"),
        bool(GridValue & 1),
        "features" if GroupValue else "none",
    )
