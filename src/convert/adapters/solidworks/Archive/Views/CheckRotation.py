from math import isclose as IsClose
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# orthographic view inputs must preserve rigid orientation rather than encode shear or reflection
def CheckRotation(MatrixValues: tuple[float, ...]) -> None:
    if type(CastValue(object, MatrixValues)) is not tuple or len(MatrixValues) != 9:
        raise ValueError("view rotation must be an immutable nine coefficient matrix")
    Numbers = tuple(RequireScalar(Value) for Value in MatrixValues)
    MatrixRows = tuple(Numbers[Offset : Offset + 3] for Offset in (0, 3, 6))
    for RowIndex, AlphaRow in enumerate(MatrixRows):
        for ColIndex, BravoRow in enumerate(MatrixRows):
            DotValue = sum(
                Alpha * Bravo for Alpha, Bravo in zip(AlphaRow, BravoRow, strict=True)
            )
            if not IsClose(
                DotValue, float(RowIndex == ColIndex), rel_tol=0.0, abs_tol=1e-12
            ):
                raise ValueError("view rotation rows must be orthonormal")
    Determinant = (
        Numbers[0] * (Numbers[4] * Numbers[8] - Numbers[5] * Numbers[7])
        - Numbers[1] * (Numbers[3] * Numbers[8] - Numbers[5] * Numbers[6])
        + Numbers[2] * (Numbers[3] * Numbers[7] - Numbers[4] * Numbers[6])
    )
    if not IsClose(Determinant, 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("view rotation must preserve orientation")
