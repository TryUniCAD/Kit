from collections.abc import Mapping

from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedDrawNumber,
)
from interchange.assembly.TransformMatrix import TransformMatrix


# native identity orientation still uses an independent sheet scale and translation
def ReadViewMatrix(
    Transform: Mapping[str, object], ScaleValue: float
) -> TransformMatrix:
    if Transform.get("has_matrix") != 0 or Transform.get("f78") != 0 or ScaleValue <= 0:
        raise ValueError("unsupported SOLIDWORKS drawing view transform mode")
    OffsetX = NeedDrawNumber(Transform.get("f58"))
    OffsetY = NeedDrawNumber(Transform.get("f60"))
    OffsetZ = NeedDrawNumber(Transform.get("f68"))
    return TransformMatrix(
        values=(
            ScaleValue,
            0.0,
            0.0,
            OffsetX,
            0.0,
            ScaleValue,
            0.0,
            OffsetY,
            0.0,
            0.0,
            ScaleValue,
            OffsetZ,
            0.0,
            0.0,
            0.0,
            1.0,
        )
    )
