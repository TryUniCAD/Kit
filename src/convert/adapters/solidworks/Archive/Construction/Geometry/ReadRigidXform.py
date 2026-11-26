from collections.abc import Mapping
from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Geometry.CrossVector import (
    CrossVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.DotVector import (
    DotVector,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)


# construction accepts only proper rigid native placements before deriving cached endpoint geometry
def ReadRigidXform(
    Fields: Mapping[str, object],
) -> tuple[tuple[float, ...], tuple[float, float, float]]:
    if (
        RequireScalar(Fields.get("f70")) != 1
        or FieldInt(Fields, "f78") != 0
        or FieldInt(Fields, "has_matrix") not in (0, 1)
    ):
        raise ValueError(
            "mate construction requires an ordinary rigid native transform"
        )
    Values = (
        RequireRecord(Fields.get("f08"))
        if Fields["has_matrix"]
        else {f"m{Index}": float(Index in (0, 4, 8)) for Index in range(9)}
    )
    Matrix = tuple(RequireScalar(Values.get(f"m{Index}")) for Index in range(9))
    RowsValue = tuple(
        (Matrix[Index], Matrix[Index + 1], Matrix[Index + 2]) for Index in (0, 3, 6)
    )
    if any(
        not IsClose(
            DotVector(First, Second),
            float(FirstIndex == SecondIndex),
            rel_tol=1e-10,
            abs_tol=1e-12,
        )
        for FirstIndex, First in enumerate(RowsValue)
        for SecondIndex, Second in enumerate(RowsValue)
    ) or not IsClose(
        DotVector(RowsValue[0], CrossVector(RowsValue[1], RowsValue[2])),
        1.0,
        rel_tol=1e-10,
        abs_tol=1e-12,
    ):
        raise ValueError("mate placement matrix must be proper and orthonormal")
    return Matrix, (
        RequireScalar(Fields.get("f58")),
        RequireScalar(Fields.get("f60")),
        RequireScalar(Fields.get("f68")),
    )
