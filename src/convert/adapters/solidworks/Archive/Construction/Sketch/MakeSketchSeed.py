from convert.adapters.solidworks.Archive.Construction.Sketch.EmptySketchRows import (
    EmptySketchRows,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeSketchDims import (
    MakeSketchDims,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeSketchMgr import (
    MakeSketchMgr,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.SketchArrays import (
    KSketchArrays,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the local sketch constructor must retain its profile backlink and distinguish constructor solver state from solved state
def MakeSketchSeed(ProfileValue: ArchiveNode) -> ArchiveNode:
    CreationValue = {f"f{OffsetValue:02x}": 1 for OffsetValue in range(0x08, 0x40, 4)}
    CreationValue["f40"] = 0
    FieldsValue = EmptySketchRows(KSketchArrays)
    FieldsValue.update(
        {
            "dims": MakeSketchDims(),
            "f12c": 1,
            "f128": 1,
            "f130": 1,
            "f140": CreationValue,
            "f37c": 0,
            "f188": 0,
            "f18c": 0,
            "f190": 0,
            "f448": {"f08": "", "lw": {"f06": -1, "f00": -1.0}, "f10": -1, "f14": 1},
            "f568": -1,
            "f570": {"x": 0.0, "y": 0.0, "z": 0.0},
            "f56c": 1,
            "f578": 0,
            "f134": 0,
            "f138": ProfileValue,
        }
    )
    FieldsValue.update(MakeSketchMgr())
    return ArchiveNode(RuntimeClass("sgSketch", 1), FieldsValue)
