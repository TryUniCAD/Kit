from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismClasses import (
    KPrismClasses,
)

# the one circle profile adds only its actual radial parameter display and handle owners to the ordinary part inventory
KCircleClasses = KPrismClasses | frozenset(
    (
        "moDisplayRadialDim_c",
        "moSkDimHandleRadial_c",
        "sgArcHandle",
        "sgCircleDim",
        "sgEntHandle",
    )
)
