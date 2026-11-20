from tests.Convert.Solidworks.Configuration.ReadMatCase import ReadMatCase


# the original density owner and authored class references need independent positions
def TestLadderMat() -> None:
    ReportValue = ReadMatCase("ladder")
    assert ReportValue["group_interval"] == [2814, 3032]
    assert ReportValue["counter"] == [49, 57]
    assert ReportValue["header_standalone_slot"] == 69
    assert ReportValue["native"] == {
        "hatch": 50,
        "material": 52,
        "density": 54,
        "density_value": 1000.0,
        "model_data": 56,
        "model_word": 0,
    }
    assert ReportValue["authored"] == {
        "bytes": 105,
        "counter": [57, 61],
        "slots": [57, 58, 59, 60],
        "spans": [[0, 52], [52, 89], [54, 89], [89, 97]],
        "hatch": [["A", "Kit hatch"], -0.375, 1.5, -7, 21, -3, 5, -9, 6],
        "density": [-31, -27, 1234.5, 0],
        "model_word": -11,
    }
    assert ReportValue["refusals"] == [
        "truncated",
        "trailing",
        "wrong_version",
        "wrong_conditions",
        "detached_part",
        "null_hatch",
        "borrowed_hatch",
        "wrong_role",
        "null_density",
        "borrowed_density",
        "wrong_density_class",
        "density_override",
        "density_name_alias",
        "null_model_data",
        "scene_alias",
        "scene_body",
        "body_visual_rows",
        "body_visual_properties",
    ]
