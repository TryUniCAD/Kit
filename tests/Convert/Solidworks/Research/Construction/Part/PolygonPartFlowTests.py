from math import isclose as IsClose
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Construction.Part.AssertPartFlow import (
    AssertPartFlow,
)
from tests.Convert.Solidworks.Research.Construction.Part.MakePolygonCase import (
    MakePolygonCase,
)
from tests.Convert.Solidworks.Research.Construction.Part.RunPartPhase import (
    RunPartPhase,
)


# distinct convex and concave parts must preserve every linked stream and actual profile shape in guarded processes
def TestPolygonPart() -> None:
    CasesValue = (
        (
            "sdk scalene triangle",
            ((-3.0, -6.0), (17.0, -6.0), (-3.0, 6.0)),
            120.0,
            False,
        ),
        (
            "sdk concave profile",
            (
                (-8.0, -5.0),
                (12.0, -5.0),
                (12.0, 2.0),
                (0.0, 2.0),
                (0.0, 10.0),
                (-8.0, 10.0),
            ),
            204.0,
            True,
        ),
    )
    SizesValue: list[int] = []
    for NameValue, VerticesValue, AreaValue, IsVariant in CasesValue:
        InputValue = MakePolygonCase(NameValue, VerticesValue, IsVariant)
        BuildValue = RunPartPhase(InputValue, "build", "polygon")
        PreparedRequest: dict[str, object] = {
            "request": InputValue,
            "build": BuildValue,
        }
        Prepared = RunPartPhase(PreparedRequest, "prepare", "polygon")
        Counterpart = RunPartPhase(PreparedRequest, "counterpart")
        SizesValue.append(AssertPartFlow(BuildValue, Prepared, Counterpart, 15))
        TargetArea = AreaValue * 1e-6
        GeometryValue = CastValue(dict[str, float], BuildValue["analytic_geometry"])
        assert IsClose(
            GeometryValue["volume_m3"],
            TargetArea * CastValue(float, BuildValue["depth_m"]),
            rel_tol=1e-12,
        )
        assert len(CastValue(list[object], BuildValue["vertices_m"])) == len(
            VerticesValue
        )
    assert SizesValue[0] != SizesValue[1]
