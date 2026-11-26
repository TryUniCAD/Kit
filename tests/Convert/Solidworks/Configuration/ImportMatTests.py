from tests.Convert.Solidworks.Configuration.ReadMatCase import ReadMatCase


# a missing material must introduce no graph slots before the model data owner
def TestConcaveMat() -> None:
    ReportValue = ReadMatCase("concave")
    assert ReportValue["group_interval"] == [1942, 2085]
    assert ReportValue["counter"] == [46, 50]
    assert ReportValue["header_standalone_slot"] == 15
    assert ReportValue["native"] == {
        "hatch": 47,
        "material": None,
        "density": None,
        "density_value": None,
        "model_data": 49,
        "model_word": 0,
    }
