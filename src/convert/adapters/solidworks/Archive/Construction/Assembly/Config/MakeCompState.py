from convert.adapters.solidworks.Archive.Construction.Assembly.Config.MakeAsmOptions import (
    MakeAsmOptions,
)
from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# each assembly configuration begins with its own componentless state and independent empty child collections before ordinary occurrences are registered
def MakeCompState() -> ArchiveNode:
    FieldsValue: dict[str, object] = {
        "f08": MakeAsmOptions(),
        "f10": None,
        "f28": {"f08": "", "f10": -1},
        "f40": None,
        "f48": {
            "f08": EmptyRootRows(),
            "f28": 101,
        },
        "f18": 0x111,
        "f20": 0,
        "f148": 0,
        "has_f140": 0,
        "has_f170": 0,
        "fc0": None,
        "fc8": None,
        "f178": "",
        "f190": 0,
    }
    FieldsValue.update(
        {FieldName: EmptyRootRows() for FieldName in ("f78", "f118", "fd0")}
    )
    return ArchiveNode(RuntimeClass("moConfigObject_c", 1), FieldsValue)
