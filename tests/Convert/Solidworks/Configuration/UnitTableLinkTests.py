from tests.Convert.Solidworks.Configuration.ReadUnitCase import ReadUnitCase
from tests.Convert.Solidworks.Configuration.UnitCaseRefusals import KCommonRefusals


# the second physical table has distinct units and resolves the original class positions
def TestUnitsLink() -> None:
    ReportValue = ReadUnitCase("concave")
    assert ReportValue["archive_version"] == 19000
    assert ReportValue["tables"] == [
        {
            "bytes": 1421,
            "rows": 16,
            "root_index": 9,
            "next_index": 42,
            "shared_classes": 0,
            "schema_count": 19,
            "field_projection_sha256": (
                "ab799cfcfca7e7ace2357626eb892ec213a90c5f63fae7546503ac1d31c618a4"
            ),
            "length": [4, 0.01, 0],
            "length_override_index": None,
            "angle": 0,
            "density_override": 0,
            "system": 4,
        },
        {
            "bytes": 1055,
            "rows": 16,
            "root_index": 60,
            "next_index": 77,
            "shared_classes": 17,
            "schema_count": 19,
            "field_projection_sha256": (
                "04cd2b5acb9309198132b624b484b9ddd694dcb7e8e033c421d4340edef543ea"
            ),
            "length": [4, 0.01, 2],
            "length_override_index": None,
            "angle": 3,
            "density_override": 0,
            "system": 1,
        },
    ]
    assert ReportValue["refusals"] == [
        *KCommonRefusals,
        "absent_class_seed",
        "wrong_seed_kind",
    ]
