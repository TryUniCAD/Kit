from convert.adapters.solidworks.Archive.Construction.Geometry.IdentityXform import (
    IdentityXform,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedDrawNumber,
)


# translated native view frames must retain the explicit authored scale and an independent rotation mapping
def MakeViewFrame(
    PointValue: tuple[float, ...],
    ScaleValue: float,
    RotationValue: dict[str, object] | None = None,
) -> dict[str, object]:
    if len(PointValue) != 3 or NeedDrawNumber(ScaleValue) <= 0:
        raise ValueError(
            "drawing frame requires a positive scale and three coordinates"
        )
    Result = IdentityXform() if RotationValue is None else dict(RotationValue)
    Result.update(
        zip(
            ("f58", "f60", "f68"),
            (NeedDrawNumber(Value) for Value in PointValue),
            strict=True,
        )
    )
    Result["f70"] = ScaleValue
    return Result
