from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmInput import (
    MakeAsmInput,
)


# independent rotated and translated authored cases vary geometry mate kind principal axis and text before any generated archive or native comparison exists
def MakeAsmCase(KindValue: str, AxisValue: str, IsVariant: bool) -> dict[str, object]:
    Request = MakeAsmInput(
        "Sdk"
        + KindValue.title()
        + AxisValue.upper()
        + ("Beta" if IsVariant else "Alpha"),
        IsVariant,
    )
    BasisValue = (
        ((0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        if IsVariant
        else ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    )
    AxisIndex = {"x": 0, "y": 1, "z": 2}[AxisValue]
    OriginValue = (0.0017, -0.0023, 0.0031)
    DistanceValue = (
        0.01953
        if KindValue == "distance"
        else 0.00731 if KindValue == "parallel" else 0.0
    )
    OtherOrigin = tuple(
        Value + 0.1074 * Tangent + DistanceValue * Normal
        for Value, Tangent, Normal in zip(
            OriginValue,
            BasisValue[(AxisIndex + 1) % 3],
            BasisValue[AxisIndex],
            strict=True,
        )
    )
    ChildValue = CastValue(dict[str, object], Request["child"])
    ChildSettings = CastValue(dict[str, object], ChildValue["settings"])
    OutputValue = CastValue(dict[str, str], ChildSettings["output"])
    ChildName = OutputValue["path_name"].rsplit("\\", 1)[-1].rsplit(".", 1)[0]
    Request["occurrences"] = [
        {
            "name": ChildName + "-1",
            "origin": OriginValue,
            "u": BasisValue[0],
            "v": BasisValue[1],
        },
        {
            "name": ChildName + "-2",
            "origin": OtherOrigin,
            "u": BasisValue[0],
            "v": BasisValue[1],
        },
    ]
    Request["mate"] = {
        "kind": KindValue,
        "name": "Authored" + KindValue.title(),
        "axis": AxisValue,
        "fixed_occurrence": int(IsVariant),
        "distance_m": DistanceValue,
        "design_intent": False,
        "selected_leader": 0,
    }
    return Request
