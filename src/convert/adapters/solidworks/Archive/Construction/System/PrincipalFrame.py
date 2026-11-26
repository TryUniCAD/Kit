from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)


# principal plane frames must preserve the native ordered tangents and signed zero arithmetic before deriving their positive normal
def PrincipalFrame(AxisValue: str) -> PlaneFrame:
    if AxisValue not in ("x", "y", "z"):
        raise ValueError("principal plane requires a positive canonical axis")
    AxisX = (1.0, 0.0, 0.0)
    AxisY = (0.0, 1.0, 0.0)
    AxisZ = (0.0, 0.0, 1.0)
    FirstValue = AxisX if AxisValue != "x" else (-AxisZ[0], -AxisZ[1], -AxisZ[2])
    SecondValue = AxisY if AxisValue != "y" else (-AxisZ[0], -AxisZ[1], -AxisZ[2])
    NormalValue = (
        FirstValue[1] * SecondValue[2] - FirstValue[2] * SecondValue[1],
        FirstValue[2] * SecondValue[0] - FirstValue[0] * SecondValue[2],
        FirstValue[0] * SecondValue[1] - FirstValue[1] * SecondValue[0],
    )
    return PlaneFrame((0.0, 0.0, 0.0), FirstValue, SecondValue, NormalValue)
