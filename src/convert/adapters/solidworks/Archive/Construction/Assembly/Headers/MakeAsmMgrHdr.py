from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.AsmTargetStamps import (
    AsmTargetStamps,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)


# the fresh assembly manager header projects its actual independent active configuration and folded generated target state without borrowing a saved part header
def MakeAsmMgrHdr(StateValue: AssemblyState, SavedAt: int) -> ArchiveNode:
    ConfigValue = StateValue.CurrentConfig
    Values = ConfigValue.FieldsValue
    ManagerValue = StateValue.ManagerValue.FieldsValue
    if (
        ManagerValue["f360"] is not ConfigValue
        or ManagerValue["f368"] is not ConfigValue
        or Values.get("owner") is not StateValue.RootValue
    ):
        raise ValueError(
            "assembly manager header requires its actual active configuration"
        )
    if (
        Values["f6a0"] is not None
        or Values.get("fbe0", 0)
        or Values.get("fbf0", 0)
        or Values["f2f0"] is not None
    ):
        raise ValueError(
            "assembly manager header requires the qualified independent configuration profile"
        )
    GeometryValue, TransformValue = AsmTargetStamps(StateValue.RootValue)
    NameValue = ReadNodeName(ConfigValue)
    EntryValue = ArchiveNode(
        RuntimeClass("dmConfigHeader_c", 1),
        {
            "f08": 1,
            "f10": NameValue,
            "f30": Values["f08"],
            "f38": Values["f860"],
            "f18": Values["f1f8"] or NameValue,
            "f34": -1,
            "f40": int(
                FieldInt(Values, "f968") != 1 and bool(FieldInt(Values, "f0c") & 8)
            ),
            "f20": Values["f4a8"],
            "f28": Values["f498"],
            "f44": Values["f4c4"],
            "f48": Values["fbd0"],
            "f50": GeometryValue,
            "f4c": TransformValue,
        },
    )
    return ArchiveNode(
        RuntimeClass("dmConfigMgrHeader_c", 1),
        {
            "f08": {"n": 1, "items": [{"o": EntryValue}]},
            "f60": SavedAt,
            "f68": ManagerValue["f75c"],
        },
    )
