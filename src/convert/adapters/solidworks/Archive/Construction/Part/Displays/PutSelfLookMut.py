from convert.adapters.solidworks.Archive.Construction.Part.Displays.MakeHolderLook import (
    BindSelfLookMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.PartSelfView import (
    PartSelfView,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PartLookInput import (
    PartLookInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PutRenderMut import (
    PutRenderMut,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph


# the modeled self state attaches its appearance before the part streams consume their actual owners
def PutSelfLookMut(
    SystemValue: PartSystem, Definition: ModelDefGraph, ViewValue: PartSelfView
) -> None:
    if (
        type(ViewValue) is not PartSelfView
        or ViewValue.StateName != "<Default>_Display State 1"
    ):
        raise ValueError(
            "part self visibility requires the default constructor appearance intent"
        )
    Appearance = ViewValue.AppearanceValue
    ConfigValue = SystemValue.ConfigValues[0]
    if type(Appearance) is PartLookInput:
        PutRenderMut(SystemValue.RootValue, ConfigValue, Definition, Appearance)
    elif Appearance == "constructor":
        BindSelfLookMut(ConfigValue)
    else:
        raise ValueError(
            "part self visibility requires the default constructor appearance intent"
        )
