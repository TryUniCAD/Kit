from math import hypot as Hypot, isfinite as IsFinite, ulp as FloatStep
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# the stored chooser bounds describe the retained inactive cylinder rather than the edited live depth
def CheckCacheBox(Bounds: ArchiveNode, CircleValue: LocalCircle, Depth: float) -> None:
    Fields = Bounds.FieldsValue
    Center = NativeRecord(Fields.get("f10"))
    Diameter = 2 * CircleValue.RadiusValue / 1000
    Expected = (*CircleValue.CenterMetres, Depth / 2, Hypot(Diameter, Diameter, Depth))
    if Fields.get("f08") != 1:
        raise ValueError("SOLIDWORKS attached circle has alternate chooser bounds")
    for Value, Target in zip(
        (Center.get("x"), Center.get("y"), Center.get("z"), Fields.get("f28")),
        Expected,
        strict=True,
    ):
        if (
            type(Value) is not float
            or not IsFinite(Value)
            or abs(Value - Target) > 4 * FloatStep(Target)
        ):
            raise ValueError(
                "SOLIDWORKS attached circle chooser bounds disagree with its inactive depth"
            )
