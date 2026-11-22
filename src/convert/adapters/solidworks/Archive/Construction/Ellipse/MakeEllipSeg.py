from convert.adapters.solidworks.Archive.Construction.Ellipse.MakeEllipPoints import (
    KPointRoles,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.EntityFields import (
    EntityFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# future native rebuild requires both segment endpoints to refer to the same distinct seam
def MakeEllipSeg(
    SketchValue: ArchiveNode, PointValues: dict[str, ArchiveNode]
) -> ArchiveNode:
    Ordinals = {RoleName: IndexValue for IndexValue, RoleName in enumerate(KPointRoles)}
    SeamValue = PointValues["seam"]
    FieldsValue = EntityFields(SketchValue)
    AxisFields = ("fdc_s", "fe0_s", "fe4_s", "fe8_s", "fec_s")
    AxisRoles = ("center", *KPointRoles[2:])
    FieldsValue.update(
        {
            "_start": SeamValue,
            "_end": SeamValue,
            "f08": 1,
            "f0c": 1,
            "fc8_s": Ordinals["seam"],
            "fcc_s": Ordinals["seam"],
            "fd0": 1,
            "fd4": 0,
            "seg_tol": -1.0,
            "fd8": 1,
            **{
                NameValue: Ordinals[RoleName]
                for NameValue, RoleName in zip(AxisFields, AxisRoles, strict=True)
            },
        }
    )
    return ArchiveNode(RuntimeClass("sgEllipse", 1), FieldsValue)
