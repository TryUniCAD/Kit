from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint


def CenteredMass(
    MassValues: dict[str, float],
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    Volume = MassValues["volume"]
    if Volume == 0.0:
        raise ValueError("Fusion closed Form mass needs a nonzero volume")
    Center = tuple(MassValues[AxisName] / Volume for AxisName in ("x", "y", "z"))
    Second = [
        MassValues[KeyName] - Volume * Center[AxisIndex] * Center[AxisIndex]
        for AxisIndex, KeyName in ((0, "xx"), (1, "yy"), (2, "zz"))
    ]
    Products = [
        MassValues["xy"] - Volume * Center[0] * Center[1],
        MassValues["xz"] - Volume * Center[0] * Center[2],
        MassValues["yz"] - Volume * Center[1] * Center[2],
    ]
    return (
        MakePoint(*Center),
        MakePoint(Second[1] + Second[2], Second[0] + Second[2], Second[0] + Second[1]),
        MakePoint(-Products[0], -Products[1], -Products[2]),
    )
