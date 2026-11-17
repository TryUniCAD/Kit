from collections.abc import Mapping

from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedDrawNumber,
)
from interchange.assembly.TransformMatrix import TransformMatrix


# native column application needs row major layout and the effective affine scale
def ReadViewMatrix(
    Transform: Mapping[str, object], ScaleValue: float
) -> TransformMatrix:
    HasMatrix = Transform.get("has_matrix")
    if HasMatrix not in (0, 1) or Transform.get("f78") != 0 or ScaleValue <= 0:
        raise ValueError("unsupported SOLIDWORKS drawing view transform mode")
    if HasMatrix == 1:
        SavedBasis = NeedConceptMap(Transform.get("f08"))
        Basis = tuple(NeedDrawNumber(SavedBasis.get(f"m{Index}")) for Index in range(9))
    else:
        Basis = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    EffectiveScale = 1.0 if abs(ScaleValue - 1.0) <= 1e-8 else ScaleValue
    Matrix = TransformMatrix(
        values=(
            Basis[0] * EffectiveScale,
            Basis[3] * EffectiveScale,
            Basis[6] * EffectiveScale,
            NeedDrawNumber(Transform.get("f58")),
            Basis[1] * EffectiveScale,
            Basis[4] * EffectiveScale,
            Basis[7] * EffectiveScale,
            NeedDrawNumber(Transform.get("f60")),
            Basis[2] * EffectiveScale,
            Basis[5] * EffectiveScale,
            Basis[8] * EffectiveScale,
            NeedDrawNumber(Transform.get("f68")),
            0.0,
            0.0,
            0.0,
            1.0,
        )
    )
    if not Matrix.IsFinite():
        raise ValueError("SOLIDWORKS drawing view transform exceeds finite range")
    return Matrix
