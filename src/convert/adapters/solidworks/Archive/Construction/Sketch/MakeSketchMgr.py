from convert.adapters.solidworks.Archive.Construction.Sketch.EmptySketchRows import (
    EmptySketchRows,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# fresh relation block loop and slot managers need complete native constructor framing without derived caches
def MakeSketchMgr() -> dict[str, object]:
    BlocksValue = EmptySketchRows((("n", "blocks"), ("m", "map")))
    BlocksValue["f40"] = EmptySketchRows((("n", "items"),))
    SlotsValue = EmptySketchRows((("n", "slots"),))
    SlotsValue["f10"] = 0
    return {
        "f590": {
            "f78": EmptySketchRows((("n", "items"),)),
            "f40": EmptySketchRows((("n", "vars"),)),
        },
        "coinc": EmptySketchRows(
            tuple((f"m{IndexValue}_n", f"m{IndexValue}") for IndexValue in range(4))
        ),
        "f5d8": ArchiveNode(
            RuntimeClass("suObList", 1), EmptySketchRows((("n", "items"),))
        ),
        "f580": BlocksValue,
        "f598": EmptySketchRows((("n", "loops"),)),
        "f588": SlotsValue,
    }
