from typing import cast as CastValue


# a third occurrence needs its own references while sharing the same fixed anchor
def AddThirdMate(Request: dict[str, object]) -> None:
    Bundle = CastValue(dict[str, object], Request["bundle"])
    Mates = CastValue(list[dict[str, object]], Bundle["mates"])
    Mates.reverse()
    Mates.insert(
        0,
        {
            "kind": "parallel",
            "name": "ThirdFrontParallel",
            "alignment": "aligned",
            "fixed_occurrence": 1,
            "endpoints": [
                {"occurrence": 1, "datum": "Front Plane"},
                {"occurrence": 2, "datum": "Front Plane"},
            ],
        },
    )
