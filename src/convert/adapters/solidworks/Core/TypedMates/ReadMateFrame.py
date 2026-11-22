from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# the ordinary plane projection must reject scale shear and reflection before applying its rigid frame rule
def ReadMateFrame(Values: tuple[float, ...]) -> tuple[float, ...]:
    Matrix = tuple(RequireScalar(Value) for Value in Values)
    if (
        len(Matrix) != 16
        or any(Matrix[Index] != 0 for Index in (3, 7, 11))
        or Matrix[15] != 1
    ):
        raise ValueError("typed mate occurrence is not an ordinary affine placement")
    RowsValue = tuple(Matrix[Index : Index + 3] for Index in (0, 4, 8))
    for First in range(3):
        for Second in range(3):
            Product = sum(
                RowsValue[First][AxisIndex] * RowsValue[Second][AxisIndex]
                for AxisIndex in range(3)
            )
            if not IsClose(
                Product, float(First == Second), rel_tol=1e-10, abs_tol=1e-12
            ):
                raise ValueError("typed mate occurrence is not a rigid placement")
    Determinant = sum(
        RowsValue[0][AxisIndex]
        * (
            RowsValue[1][(AxisIndex + 1) % 3] * RowsValue[2][(AxisIndex + 2) % 3]
            - RowsValue[1][(AxisIndex + 2) % 3] * RowsValue[2][(AxisIndex + 1) % 3]
        )
        for AxisIndex in range(3)
    )
    if not IsClose(Determinant, 1.0, rel_tol=1e-10, abs_tol=1e-12):
        raise ValueError("typed mate occurrence is not a proper rigid placement")
    return Matrix
