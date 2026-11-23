from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import (
    AsmDisplayIn,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.CheckSelfVisual import (
    CheckSelfVisual,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.PartSelfView import (
    PartSelfView,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PartLookInput import (
    PartLookInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.VisualStates.WriteAsmVisual import (
    KVisualStream,
)


# the singleton parent may reference a modeled radial view with its actual independent child allocator
def CheckCylSelfVis(
    ChildValue: PartCandidate, DisplayValues: tuple[AsmDisplayIn, ...]
) -> None:
    ViewValue = ChildValue.SelfView
    if ViewValue is None:
        if KVisualStream in ChildValue.StreamsValue:
            raise ValueError(
                "assembly visibility requires the ordinary radial child without a visual store"
            )
        return
    if (
        type(ViewValue) is not PartSelfView
        or type(ViewValue.AppearanceValue) is not PartLookInput
        or type(DisplayValues) is not tuple
        or len(DisplayValues) != 1
    ):
        raise ValueError(
            "concentric child appearance requires its named look and singleton parent state"
        )
    CheckSelfVisual(ChildValue)
    if WriteModelDef(
        ChildValue.DefinitionValue
    ).OutputValue != ChildValue.StreamsValue.get("Contents/Definition"):
        raise ValueError(
            "concentric child appearance Definition disagrees with its graph"
        )
