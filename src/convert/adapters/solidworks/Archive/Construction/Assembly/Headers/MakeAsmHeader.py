from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import (
    HeaderInput,
)
from convert.adapters.solidworks.Archive.Construction.Header.HeaderZeroes import (
    KHeaderZeroes,
)
from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import (
    MakeRootLog,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# assembly header construction derives counters and revision ownership from its actual root while retaining explicit fresh provenance and absent external directory
def MakeAsmHeader(
    StateValue: AssemblyState, InputValue: HeaderInput, ModelPresent: bool
) -> ArchiveNode:
    UserValue = ArchiveNode(
        RuntimeClass("su_CStringArray", 0),
        {"values": (CStringValue(InputValue.AuthorName, True),)},
    )
    CompanyValue = ArchiveNode(
        RuntimeClass("su_CStringArray", 0),
        {"values": (CStringValue(InputValue.CompanyName, True),)},
    )
    LogsValue = ArchiveNode(
        RuntimeClass("suObList", 1),
        {"items": (MakeRootLog(StateValue.RootValue, InputValue),)},
    )
    FieldsValue: dict[str, object] = dict.fromkeys(KHeaderZeroes, 0)
    FieldsValue.update(
        {
            "fec": int(ModelPresent),
            "f10": UserValue,
            "f18": CompanyValue,
            "f20": LogsValue,
            "f50": InputValue.ModifiedAt,
            "f08": StateValue.Allocator.NextValue,
            "f30": None,
            "f40": 101,
            "f38": None,
            "f44": 101,
            "f70": InputValue.CreatedAt,
            "f28": None,
            "fc4": 0,
            "f7c": 0,
            "f48": InputValue.UpdatedAt,
            "f88": None,
            "bbox": None,
            "fcc": -1,
            "fd0": -1,
            "fd4": -1,
            "f80": 0,
        }
    )
    return ArchiveNode(RuntimeClass("moHeader_c", 1), FieldsValue)
