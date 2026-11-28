from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.IsDimRect import (
    IsDimRect,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# strict dimensional ownership begins only after identifying the actual supported rectangle and blind boss
def IsDimLeaf(Profile: ArchiveNode, Operation: ArchiveNode) -> bool:
    try:
        SketchValue = RequireNative(Profile.FieldsValue.get("pd_f80"), "sgSketch")
        if not IsDimRect(SketchValue):
            return False
        Reference = RequireNative(Profile.FieldsValue.get("pd_f78"), "moCompRefPlane_c")
        if Reference.FieldsValue.get("f100") != 3:
            return False
        BossValue = RequireNative(Operation, "moExtrusion_c")
        EndValue = RequireNative(BossValue.FieldsValue.get("f818"), "moEndSpec_c")
        return EndValue.FieldsValue.get("f08") == 1 and all(
            EndValue.FieldsValue.get(FieldName) == 0
            for FieldName in ("f0c", "f10", "f88", "f8c")
        )
    except (KeyError, TypeError, ValueError):
        return False
