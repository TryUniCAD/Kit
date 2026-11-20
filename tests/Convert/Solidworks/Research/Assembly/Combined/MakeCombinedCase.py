from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Assembly.PlanarMateInput import MakeMateInput


# independent placement sets exercise two constraints on one pair and another on a third occurrence
def MakeMateCase(IncludeThird: bool) -> dict[str, object]:
    Request = MakeMateInput("combined")
    Bundle = CastValue(dict[str, object], Request["bundle"])
    Occurrences = CastValue(list[dict[str, object]], Bundle["occurrences"])
    Moving = CastValue(dict[str, object], Occurrences[0]["placement"])
    Mates = CastValue(list[dict[str, object]], Bundle["mates"])
    Moving["origin"] = [Mates[0]["distance_m"], 0.0, 0.00825]
    Mates.append(
        {
            "kind": "coincident",
            "name": "TopCoincident",
            "alignment": "aligned",
            "fixed_occurrence": 1,
            "endpoints": [
                {"occurrence": 1, "datum": "Top Plane"},
                {"occurrence": 0, "datum": "Top Plane"},
            ],
        }
    )
    if IncludeThird:
        Occurrences.append(
            {
                "name": "GeneratedChildModel-3",
                "placement": {
                    "origin": [0.038, 0.016, 0.013],
                    "u": [1.0, 0.0, 0.0],
                    "v": [0.0, 1.0, 0.0],
                },
            }
        )
    return Request
