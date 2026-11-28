from tests.Convert.Solidworks.Research.Construction.RootStyleInput import RootStyleInput


# root component requests must contain explicit metadata units and allocator state without unrelated geometry
def RootCaseInput(
    NameValue: str, NextValue: int, Reserved: tuple[int, ...]
) -> dict[str, object]:
    return {
        "name": NameValue,
        "hatch_name": NameValue + " hatch",
        "next_id": NextValue,
        "reserved_ids": list(Reserved),
        "document_units": {
            "length_unit": "mm",
            "angle_unit": "degree",
            "unit_system": "mmgs",
            "decimal_places": 4,
        },
        "analysis_units": {
            "length_unit": "m",
            "angle_unit": "radian",
            "unit_system": "mks",
            "decimal_places": 6,
        },
        "styles": RootStyleInput(NameValue),
        "provenance": {
            "author": "Kit research",
            "company": "authored root experiment",
            "created_at": 1700000000 + NextValue,
            "comment": "generated native root ownership",
        },
    }
