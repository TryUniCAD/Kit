from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Assembly.OccurrenceInput import MakeOccInput

# a distinctive authored length separates the driving parameter from the initial plane gap
KMateLength = 0.06725

# reused authored placement lets the test distinguish each ordered endpoint independently
KMovingOrigin = (0.034, -0.006, 0.009)

# the guarded builder and command need stable filenames for the related native archives
KAssemblyName = "ProjectedPlaneMate"


# reverse selection order exercises native occurrence links beyond the model list order
def MakeMateInput(ChildFolder: str) -> dict[str, object]:
    AxisX, AxisY = [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]
    Bundle = MakeOccInput(KAssemblyName, list(KMovingOrigin), AxisX, AxisY)
    Assembly = CastValue(dict[str, object], Bundle["assembly"])
    Presentation = CastValue(dict[str, object], Assembly["presentation"])
    Presentation.update(design_intent=False, selected_leader=0)
    Child = CastValue(dict[str, object], Bundle["child"])
    Output = CastValue(dict[str, object], Child["output"])
    Output["path_name"] = f"C:\\generated\\{ChildFolder}\\GeneratedChildFile.SLDPRT"
    Occurrences = CastValue(list[dict[str, object]], Bundle["occurrences"])
    Occurrences.append(
        {
            "name": "GeneratedChildModel-2",
            "placement": {"origin": [0.0, 0.0, 0.0], "u": AxisX, "v": AxisY},
        }
    )
    Bundle["mates"] = [
        {
            "kind": "distance",
            "name": "ProjectedDistance",
            "alignment": "aligned",
            "fixed_occurrence": 1,
            "distance_m": KMateLength,
            "endpoints": [
                {"occurrence": 1, "datum": "Right Plane"},
                {"occurrence": 0, "datum": "Right Plane"},
            ],
        }
    ]
    return {"bundle": Bundle, "include_xml_metadata": True}
