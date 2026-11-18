from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Assembly.OccurrenceInput import MakeOccInput
from tests.Convert.Solidworks.Research.Mates.Construction.MateDesigns import (
    KContours,
    KDatumNames,
)


# authored positive gaps remain independent from driving lengths while axes contours placements and presentation vary without native inputs
def MakeDistInput(AxisValue: str, LengthValue: float = 0.071375) -> dict[str, object]:
    AxisFirst = [1.0, 0.0, 0.0] if AxisValue == "x" else [0.6, 0.8, 0.0]
    AxisSecond = [0.0, 1.0, 0.0] if AxisValue == "x" else [-0.8, 0.6, 0.0]
    Normal = {"x": (1.0, 0.0, 0.0), "y": (-0.8, 0.6, 0.0), "z": (0.0, 0.0, 1.0)}[
        AxisValue
    ]
    First = [0.0027, -0.0191, 0.0063]
    Second = [
        Value + 0.043875 * UnitValue
        for Value, UnitValue in zip(First, Normal, strict=True)
    ]
    Bundle = MakeOccInput(
        "SdkDistance" + AxisValue.upper(), Second, AxisFirst, AxisSecond
    )
    Assembly = CastValue(dict[str, object], Bundle["assembly"])
    Presentation = CastValue(dict[str, object], Assembly["presentation"])
    Presentation.update(
        design_intent=AxisValue == "z", selected_leader=int(AxisValue == "y")
    )
    ChildValue = CastValue(dict[str, object], Bundle["child"])
    Document = CastValue(dict[str, object], ChildValue["document"])
    Document.update(
        vertices_m=KContours[AxisValue], depth_m=0.0089, plane_axis=AxisValue
    )
    Occurrences = CastValue(list[dict[str, object]], Bundle["occurrences"])
    Occurrences.append(
        {
            "name": "Distance anchor-2",
            "placement": {"origin": First, "u": AxisFirst, "v": AxisSecond},
        }
    )
    Bundle["mates"] = [
        {
            "kind": "distance",
            "name": "Driving gap α " + AxisValue,
            "alignment": "aligned",
            "fixed_occurrence": 1,
            "created_at": 1794701731,
            "distance_m": LengthValue,
            "endpoints": [
                {"occurrence": Index, "datum": KDatumNames[AxisValue]}
                for Index in (1, 0)
            ],
        }
    ]
    return Bundle
