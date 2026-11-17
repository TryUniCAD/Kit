from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Assembly.OccurrenceInput import MakeOccInput
from tests.Convert.Solidworks.Research.Mates.Construction.MateDesigns import (
    KContours,
    KDatumNames,
)


# authored contour datum ordering placements and provenance exercise a complete generated bundle without native file inputs
def MakeSdkMate(KindValue: str, AxisValue: str) -> dict[str, object]:
    Rotated = AxisValue != "x"
    AxisFirst = [0.6, 0.8, 0.0] if Rotated else [1.0, 0.0, 0.0]
    AxisSecond = [-0.8, 0.6, 0.0] if Rotated else [0.0, 1.0, 0.0]
    Bundle = MakeOccInput(
        "Sdk" + KindValue.title() + AxisValue.upper(),
        [0.1074, -0.00473, 0.0123],
        AxisFirst,
        AxisSecond,
    )
    ChildValue = CastValue(dict[str, object], Bundle["child"])
    Document = CastValue(dict[str, object], ChildValue["document"])
    Document.update(
        vertices_m=KContours[AxisValue],
        depth_m=0.0089,
        plane_axis=AxisValue,
    )
    Occurrences = CastValue(list[dict[str, object]], Bundle["occurrences"])
    Occurrences.append(
        {
            "name": "Second placement " + AxisValue + "-2",
            "placement": {
                "origin": [-0.0091, 0.0179, 0.0037],
                "u": AxisFirst,
                "v": AxisSecond,
            },
        }
    )
    OrderValue = (0, 1) if AxisValue == "z" else (1, 0)
    Bundle["mates"] = [
        {
            "kind": KindValue,
            "name": "Authored " + KindValue + " α " + AxisValue,
            "alignment": "aligned",
            "fixed_occurrence": OrderValue[0],
            "created_at": 1794701729,
            "endpoints": [
                {"occurrence": Index, "datum": KDatumNames[AxisValue]}
                for Index in OrderValue
            ],
        }
    ]
    return Bundle
