from convert.adapters.solidworks.Archive.Construction.Sketch.EntityFields import (
    EntityFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the ordinary full circle joins the same seam point twice and a distinct centre with compact array references
def MakeCircleArc(
    SketchValue: ArchiveNode,
    CenterValue: ArchiveNode,
    MarkerValue: ArchiveNode,
    CenterIndex: int,
    MarkerIndex: int,
    ArcIndex: int,
) -> ArchiveNode:
    FieldsValue = EntityFields(SketchValue)
    FieldsValue.update(
        {
            "_center": CenterValue,
            "_start": MarkerValue,
            "_end": MarkerValue,
            "f08": ArcIndex + 1,
            "f0c": ArcIndex + 1,
            "fc8_s": min(MarkerIndex, 0xFFFF),
            "fc8": MarkerIndex,
            "fcc_s": min(MarkerIndex, 0xFFFF),
            "fcc": MarkerIndex,
            "fd0": 1,
            "fd4": 0,
            "seg_tol": -1.0,
            "fd8": 1,
            "fdc_s": min(CenterIndex, 0xFFFF),
            "fdc": CenterIndex,
            "fe0": -2,
            "fe4": -2,
            "fe8": -2,
            "fec": -2,
        }
    )
    return ArchiveNode(RuntimeClass("sgArc", 1), FieldsValue)
