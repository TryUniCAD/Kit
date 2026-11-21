from convert.adapters.solidworks.Archive.Construction.Part.Displays.CheckRectVisual import (
    CheckRectVisual,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.MakeChildRefs import (
    MakeChildRefs,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.MakeHolderLook import (
    MakeHolderLook,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.PartSelfView import (
    PartSelfView,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.ReadSelfOwners import (
    ReadSelfOwners,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.PartPlan import (
    KPartPlan,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.VisualStates.DetachVisualRef import (
    DetachVisualRef,
)
from convert.adapters.solidworks.Archive.VisualStates.MakeVisKey import MakeVisKey
from convert.adapters.solidworks.Archive.VisualStates.MakeVisRow import MakeVisRow
from convert.adapters.solidworks.Archive.VisualStates.WriteAsmVisual import (
    WriteAsmVisual,
)


# the part self state owns one concrete appearance attribute and keeps feature visibility in the remaining ordered rows
def MakePartVis(
    SystemValue: PartSystem,
    ProfileValue: ArchiveNode,
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    PlanValue: KPartPlan,
    ViewValue: PartSelfView,
) -> bytes:
    if (
        type(ViewValue) is not PartSelfView
        or ViewValue.StateName != "<Default>_Display State 1"
        or ViewValue.AppearanceValue != "constructor"
    ):
        raise ValueError(
            "part self visibility requires the default constructor appearance intent"
        )
    CheckRectVisual(PlanValue)
    UnitValue, Config = ReadSelfOwners(SystemValue, HeadersValue)
    Appearance = MakeHolderLook(SystemValue.RootValue, Config)
    Holder = ArchiveNode(RuntimeClass("moCompHolder_c", 1), DetachVisualRef(UnitValue))
    Features = MakeChildRefs(SystemValue, ProfileValue, HeadersValue, UnitValue)
    PropertyClass = RuntimeClass("visStateVisualPropertiesAttribute_c", 1)
    StateClass = RuntimeClass("visStateVisualStateAttribute_c", 1)
    SelfProperty = ArchiveNode(PropertyClass, {"f08": 1, "f10": Appearance})
    DatumProperty = ArchiveNode(PropertyClass, {"f08": 1, "f10": None})
    Shown = ArchiveNode(StateClass, {"f08": 1, "f10": 1, "f14": 6, "f18": 1, "f1c": 0})
    Hidden = ArchiveNode(StateClass, {"f08": 1, "f10": 0, "f14": 6, "f18": 1, "f1c": 0})
    AttrRows = [{"ref": Holder, "attrs": [MakeVisRow(1, SelfProperty, Shown)]}]
    AttrRows.extend(
        {
            "ref": Feature,
            "attrs": [MakeVisRow(1, DatumProperty, Shown if Index < 2 else Hidden)],
        }
        for Index, Feature in enumerate(Features)
    )
    return WriteAsmVisual(
        MakeVisKey(Config, (ViewValue.StateName,), [], AttrRows), PartSelf=True
    )
