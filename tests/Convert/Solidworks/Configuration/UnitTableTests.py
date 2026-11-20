from tests.Convert.Solidworks.Configuration.ReadUnitCase import ReadUnitCase
from tests.Convert.Solidworks.Configuration.UnitCaseRefusals import KCommonRefusals


# the native ladder table retains its inherited length data and distinct override
def TestUnitsLadder() -> None:
    ReportValue = ReadUnitCase("ladder")
    assert ReportValue["archive_version"] == 19000
    assert ReportValue["tables"] == [
        {
            "bytes": 1487,
            "rows": 16,
            "root_index": 9,
            "next_index": 43,
            "shared_classes": 0,
            "schema_count": 19,
            "field_projection_sha256": (
                "73fa20249382f9c982e542c3acbe6967ced9da3db9b0bf44dd99c536c21f30f9"
            ),
            "length": [2, 0.1, 0],
            "length_override_index": 12,
            "angle": 0,
            "density_override": 0,
            "system": 4,
        }
    ]
    assert ReportValue["refusals"] == [
        *KCommonRefusals,
        "wrong_map_base",
        "wrong_length_owner",
    ]
