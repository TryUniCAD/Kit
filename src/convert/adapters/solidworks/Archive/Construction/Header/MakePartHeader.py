from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import (
    HeaderInput,
)
from convert.adapters.solidworks.Archive.Construction.Header.HeaderZeroes import (
    KHeaderZeroes,
)
from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import (
    MakeRootLog,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# a fresh part header must derive its persistent counter and revision graph from the constructed model and explicit provenance
def MakePartHeader(
    OwnerValue: ArchiveNode,
    InputValue: HeaderInput,
    Allocator: PersistentIds,
    ModelPresent: bool,
) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moPart_c")
    if (
        type(InputValue) is not HeaderInput
        or type(Allocator) is not PersistentIds
        or type(ModelPresent) is not bool
    ):
        raise TypeError(
            "header construction requires explicit typed provenance and model presence"
        )
    Identifier = OwnerValue.FieldsValue.get("f08")
    if (
        type(Identifier) is not int
        or not 0 <= Identifier < Allocator.NextValue <= 0x7FFFFFFF
        or Allocator.Allocations.get((OwnerValue, "f08")) != Identifier
    ):
        raise ValueError(
            "header counter must follow the actual allocated model identifier"
        )
    UserTable = ArchiveNode(
        RuntimeClass("su_CStringArray", 0),
        {"values": (CStringValue(InputValue.AuthorName, True),)},
    )
    CompanyTable = ArchiveNode(
        RuntimeClass("su_CStringArray", 0),
        {"values": (CStringValue(InputValue.CompanyName, True),)},
    )
    LogsValue = ArchiveNode(
        RuntimeClass("suObList", 1), {"items": (MakeRootLog(OwnerValue, InputValue),)}
    )
    FieldsValue: dict[str, object] = dict.fromkeys(KHeaderZeroes, 0)
    FieldsValue.update(
        {
            "fec": int(ModelPresent),
            "f10": UserTable,
            "f18": CompanyTable,
            "f20": LogsValue,
            "f50": InputValue.ModifiedAt,
            "f08": Allocator.NextValue,
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
