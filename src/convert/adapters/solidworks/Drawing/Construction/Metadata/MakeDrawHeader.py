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
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Drawing.Construction.Model.DrawRootGraph import (
    DrawRootGraph,
)


# drawing headers must derive their counter and revision owners from the actual fresh model and explicit provenance
def MakeDrawHeader(GraphValue: DrawRootGraph, InputValue: HeaderInput) -> ArchiveNode:
    if type(GraphValue) is not DrawRootGraph or type(InputValue) is not HeaderInput:
        raise TypeError(
            "drawing header requires actual model construction and explicit typed provenance"
        )
    ModelValue = GraphValue.ModelValue
    RequireRootNode(ModelValue, "moDrawing_c")
    Identifier = ModelValue.FieldsValue.get("f08")
    if (
        type(Identifier) is not int
        or not 0 <= Identifier < GraphValue.Allocator.NextValue <= 2147483647
    ):
        raise ValueError(
            "drawing header counter must follow its actual model registration"
        )
    FieldsValue: dict[str, object] = dict.fromkeys(KHeaderZeroes, 0)
    FieldsValue.update(
        {
            "fec": 1,
            "f10": ArchiveNode(
                RuntimeClass("su_CStringArray", 0),
                {"values": (CStringValue(InputValue.AuthorName, True),)},
            ),
            "f18": ArchiveNode(
                RuntimeClass("su_CStringArray", 0),
                {"values": (CStringValue(InputValue.CompanyName, True),)},
            ),
            "f20": ArchiveNode(
                RuntimeClass("suObList", 1),
                {"items": (MakeRootLog(ModelValue, InputValue),)},
            ),
            "f50": InputValue.ModifiedAt,
            "f08": GraphValue.Allocator.NextValue,
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
